#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import xml.etree.ElementTree as ET

LEGAL_PREFIXES = (
    "LICENSE",
    "LICENCE",
    "NOTICE",
    "COPYING",
    "COPYRIGHT",
    "DEPENDENCIES",
    "ABOUT",
)
SOURCE_REQUIRED_PATTERNS = (
    "mozilla public license",
    "mpl-",
    "eclipse public license",
    "epl-",
    "gnu general public license",
    "gpl-",
    "gnu lesser general public license",
    "lgpl-",
    "common development and distribution license",
    "cddl-",
)
KNOWN_SCOPES = {"compile", "runtime", "provided", "system", "test", "import"}


@dataclass(frozen=True)
class MavenComponent:
    group: str
    artifact: str
    packaging: str
    classifier: str
    version: str
    scope: str
    artifact_path: Path

    @property
    def coordinate(self) -> str:
        classifier = f":{self.classifier}" if self.classifier else ""
        return f"{self.group}:{self.artifact}:{self.packaging}{classifier}:{self.version}"


@dataclass(frozen=True)
class NpmComponent:
    name: str
    version: str
    package_dir: Path
    resolved: str
    integrity: str


class ComplianceError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def clean_segment(value: str) -> str:
    value = value.replace("@", "at-")
    value = re.sub(r"[^A-Za-z0-9._+-]+", "_", value)
    return value.strip("._") or "unknown"


def is_legal_basename(name: str) -> bool:
    upper = name.upper()
    return any(upper.startswith(prefix) for prefix in LEGAL_PREFIXES)


def copy_legal_files_from_zip(archive_path: Path, destination: Path) -> list[str]:
    copied: list[str] = []
    if not zipfile.is_zipfile(archive_path):
        return copied
    with zipfile.ZipFile(archive_path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            member = PurePosixPath(info.filename)
            if member.is_absolute() or ".." in member.parts:
                raise ComplianceError(f"Unsafe ZIP/JAR entry in {archive_path}: {info.filename}")
            if not is_legal_basename(member.name):
                continue
            target = destination.joinpath(*member.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info))
            copied.append(info.filename)
    return sorted(set(copied))


def copy_legal_files_from_directory(source: Path, destination: Path) -> list[str]:
    copied: list[str] = []
    if not source.is_dir():
        return copied
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(source)
        except ValueError:
            continue
        if "node_modules" in rel.parts:
            continue
        if not is_legal_basename(path.name):
            continue
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied.append(rel.as_posix())
    return copied


def parse_maven_list(path: Path) -> list[MavenComponent]:
    components: list[MavenComponent] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if " -- " in line:
            line = line.split(" -- ", 1)[0].rstrip()
        if not line or line.startswith("The following") or line.startswith("none"):
            continue
        parts = line.split(":")
        if len(parts) < 6:
            continue
        artifact_path = Path(parts[-1])
        scope = parts[-2]
        if scope not in KNOWN_SCOPES or not artifact_path.is_absolute():
            continue
        version = parts[-3]
        group, artifact, packaging = parts[0], parts[1], parts[2]
        middle = parts[3:-3]
        classifier = ":".join(middle) if middle else ""
        key = (group, artifact, packaging, classifier, version)
        if key in seen:
            continue
        if not artifact_path.is_file():
            raise ComplianceError(f"Resolved Maven artifact does not exist: {artifact_path}")
        seen.add(key)
        components.append(
            MavenComponent(group, artifact, packaging, classifier, version, scope, artifact_path)
        )
    if not components:
        raise ComplianceError(f"No Maven dependencies parsed from {path}")
    return sorted(components, key=lambda c: (c.group, c.artifact, c.version, c.classifier))


def find_pom(component: MavenComponent) -> Path | None:
    parent = component.artifact_path.parent
    exact = parent / f"{component.artifact}-{component.version}.pom"
    if exact.is_file():
        return exact
    poms = sorted(parent.glob("*.pom"))
    return poms[0] if poms else None


def pom_metadata(pom_path: Path | None) -> tuple[list[str], list[str], str, list[str]]:
    if pom_path is None or not pom_path.is_file():
        return [], [], "", []
    try:
        root = ET.parse(pom_path).getroot()
    except ET.ParseError:
        return [], [], "", []

    names: list[str] = []
    urls: list[str] = []
    for license_node in root.findall("./{*}licenses/{*}license"):
        name = license_node.findtext("{*}name", default="").strip()
        url = license_node.findtext("{*}url", default="").strip()
        if name:
            names.append(name)
        if url:
            urls.append(url)

    project_url = root.findtext("./{*}url", default="").strip()
    scm_values: list[str] = []
    scm = root.find("./{*}scm")
    if scm is not None:
        for child_name in ("url", "connection", "developerConnection", "tag"):
            value = scm.findtext(f"{{*}}{child_name}", default="").strip()
            if value:
                scm_values.append(value)
    return sorted(set(names)), sorted(set(urls)), project_url, sorted(set(scm_values))


def source_jar_for(component: MavenComponent, source_root: Path) -> Path | None:
    base = source_root.joinpath(*component.group.split("."), component.artifact, component.version)
    if not base.is_dir():
        return None
    exact = base / f"{component.artifact}-{component.version}-sources.jar"
    if exact.is_file():
        return exact
    matches = sorted(base.glob(f"{component.artifact}-*-sources.jar"))
    return matches[0] if matches else None


def read_small_text_files(paths: list[Path], limit_per_file: int = 2_000_000) -> str:
    chunks: list[str] = []
    for path in paths:
        try:
            if path.stat().st_size > limit_per_file:
                continue
            chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
    return "\n".join(chunks).lower()


def parse_fat_jar_maven_coordinates(jar: Path) -> list[tuple[str, str, str]]:
    coords: set[tuple[str, str, str]] = set()
    with zipfile.ZipFile(jar) as archive:
        for info in archive.infolist():
            name = PurePosixPath(info.filename)
            if name.name != "pom.properties" or "META-INF" not in name.parts or "maven" not in name.parts:
                continue
            data = archive.read(info).decode("utf-8", errors="replace")
            values: dict[str, str] = {}
            for line in data.splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                values[k.strip()] = v.strip()
            group = values.get("groupId", "")
            artifact = values.get("artifactId", "")
            version = values.get("version", "")
            if group and artifact and version:
                coords.add((group, artifact, version))
    return sorted(coords)


def parse_npm(package_lock: Path, node_modules: Path) -> list[NpmComponent]:
    data = json.loads(package_lock.read_text(encoding="utf-8"))
    packages = data.get("packages")
    if not isinstance(packages, dict):
        raise ComplianceError("package-lock.json has no packages object")
    result: list[NpmComponent] = []
    for lock_path, meta in sorted(packages.items()):
        if not lock_path or not lock_path.startswith("node_modules/"):
            continue
        if not isinstance(meta, dict):
            continue
        name = lock_path[len("node_modules/") :]
        version = str(meta.get("version", "")).strip()
        if not name or not version:
            raise ComplianceError(f"Incomplete npm package metadata for {lock_path}")
        package_dir = node_modules / name
        if not package_dir.is_dir():
            raise ComplianceError(f"npm package directory missing: {package_dir}")
        result.append(
            NpmComponent(
                name=name,
                version=version,
                package_dir=package_dir,
                resolved=str(meta.get("resolved", "")),
                integrity=str(meta.get("integrity", "")),
            )
        )
    if not result:
        raise ComplianceError("No npm dependencies found in package-lock.json")
    return result


def package_json_metadata(path: Path) -> tuple[str, str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    license_value = data.get("license", "")
    if isinstance(license_value, dict):
        license_text = str(license_value.get("type", ""))
    else:
        license_text = str(license_value or "")
    repository = data.get("repository", "")
    if isinstance(repository, dict):
        repository_text = str(repository.get("url", ""))
    else:
        repository_text = str(repository or "")
    homepage = str(data.get("homepage", "") or "")
    return license_text.strip(), repository_text.strip(), homepage.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream-jar", required=True, type=Path)
    parser.add_argument("--maven-list", required=True, type=Path)
    parser.add_argument("--maven-sources", required=True, type=Path)
    parser.add_argument("--package-lock", required=True, type=Path)
    parser.add_argument("--node-modules", required=True, type=Path)
    parser.add_argument("--upstream-version", required=True)
    parser.add_argument("--upstream-tag", required=True)
    parser.add_argument("--upstream-repo", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    out = args.output
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    errors: list[str] = []
    warnings: list[str] = []
    rows: list[dict[str, str]] = []

    # Preserve legal resources that survived upstream shading, for traceability.
    upstream_jar_out = out / "upstream-jar"
    upstream_jar_files = copy_legal_files_from_zip(args.upstream_jar, upstream_jar_out)
    if not upstream_jar_files:
        errors.append("No legal resources were found in the upstream Bastillion JAR.")

    embedded = parse_fat_jar_maven_coordinates(args.upstream_jar)
    with (out / "JAR-EMBEDDED-MAVEN.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(["group", "artifact", "version"])
        writer.writerows(embedded)

    maven_components = parse_maven_list(args.maven_list)
    resolved_ga = {(c.group, c.artifact, c.version) for c in maven_components}
    unexpected_embedded = [
        c for c in embedded
        if c not in resolved_ga and not (c[0] == "io.bastillion" and c[1] == "bastillion")
    ]
    if unexpected_embedded:
        errors.append(
            "The upstream JAR contains Maven coordinates not present in the resolved runtime dependency set: "
            + ", ".join(":".join(c) for c in unexpected_embedded)
        )

    for component in maven_components:
        component_dir = out / "maven" / clean_segment(component.group) / clean_segment(component.artifact) / clean_segment(component.version)
        component_dir.mkdir(parents=True, exist_ok=True)

        pom = find_pom(component)
        license_names, license_urls, project_url, scm_values = pom_metadata(pom)
        if pom:
            shutil.copy2(pom, component_dir / "pom.xml")

        legal_dir = component_dir / "legal"
        binary_legal = copy_legal_files_from_zip(component.artifact_path, legal_dir / "binary-artifact")

        source_jar = source_jar_for(component, args.maven_sources)
        source_legal: list[str] = []
        source_rel = ""
        if source_jar:
            source_copy = component_dir / "source" / source_jar.name
            source_copy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_jar, source_copy)
            source_rel = source_copy.relative_to(out).as_posix()
            source_legal = copy_legal_files_from_zip(source_jar, legal_dir / "source-artifact")

        legal_paths = [p for p in legal_dir.rglob("*") if p.is_file()]
        evidence_text = " ".join(license_names + license_urls) + "\n" + read_small_text_files(legal_paths)
        source_required = any(pattern in evidence_text.lower() for pattern in SOURCE_REQUIRED_PATTERNS)

        if not legal_paths:
            errors.append(f"No full legal text/notice found for Maven component {component.coordinate}.")
        if source_required and not source_jar:
            errors.append(
                f"Source availability could not be materialized for source-requiring Maven component {component.coordinate}."
            )
        if "SNAPSHOT" in component.version.upper():
            warnings.append(
                f"{component.coordinate} is a SNAPSHOT dependency. Its generic Maven version does not identify the timestamped build used when Loophole created the already-shaded release JAR."
            )

        rows.append(
            {
                "ecosystem": "maven",
                "name": f"{component.group}:{component.artifact}",
                "version": component.version,
                "declared_license": " OR ".join(license_names),
                "license_urls": " ".join(license_urls),
                "artifact_sha256": sha256(component.artifact_path),
                "legal_files": str(len(legal_paths)),
                "source_materialized": "yes" if source_jar else "no",
                "source_path_or_url": source_rel or project_url or " ".join(scm_values),
            }
        )

    npm_components = parse_npm(args.package_lock, args.node_modules)
    for component in npm_components:
        package_json = component.package_dir / "package.json"
        if not package_json.is_file():
            errors.append(f"package.json missing for npm component {component.name}@{component.version}")
            continue
        license_text, repository, homepage = package_json_metadata(package_json)
        component_dir = out / "npm" / clean_segment(component.name) / clean_segment(component.version)
        component_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(package_json, component_dir / "package.json")
        legal_files = copy_legal_files_from_directory(component.package_dir, component_dir / "legal")
        if not legal_files:
            errors.append(f"No full legal text/notice found for npm component {component.name}@{component.version}.")
        rows.append(
            {
                "ecosystem": "npm",
                "name": component.name,
                "version": component.version,
                "declared_license": license_text,
                "license_urls": "",
                "artifact_sha256": component.integrity,
                "legal_files": str(len(legal_files)),
                "source_materialized": "no",
                "source_path_or_url": component.resolved or repository or homepage,
            }
        )

    fieldnames = [
        "ecosystem",
        "name",
        "version",
        "declared_license",
        "license_urls",
        "artifact_sha256",
        "legal_files",
        "source_materialized",
        "source_path_or_url",
    ]
    with (out / "COMPONENTS.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: (r["ecosystem"], r["name"], r["version"])))

    report = [
        "# Bastillion redistribution compliance bundle",
        "",
        f"Upstream repository: `{args.upstream_repo}`  ",
        f"Upstream tag: `{args.upstream_tag}`  ",
        f"Upstream version: `{args.upstream_version}`  ",
        f"Upstream JAR SHA-256: `{sha256(args.upstream_jar)}`",
        "",
        "This bundle supplements, and does not replace, the upstream Bastillion license.",
        "It preserves legal notices from the official shaded JAR and independently collects",
        "component-specific legal material from the resolved Maven runtime artifacts and npm",
        "packages used by the matching upstream source tag.",
        "",
        f"Maven runtime components collected: **{len(maven_components)}**  ",
        f"npm components collected: **{len(npm_components)}**  ",
        f"Legal resources surviving inside the upstream shaded JAR: **{len(upstream_jar_files)}**",
        "",
        "## Source availability",
        "",
        "Where Maven source JARs are published, they are included below each component under",
        "`maven/.../source/`. This intentionally includes more source material than is required",
        "for many permissively licensed components and ensures that source-availability obligations",
        "identified from MPL/EPL/GPL/LGPL/CDDL license evidence are not left to a bare URL.",
        "",
        "For npm components, `COMPONENTS.tsv` records the integrity value and the registry tarball",
        "URL from the upstream lock file. The full license/notice files from the installed package",
        "are retained under `npm/.../legal/`.",
        "",
        "## Upstream shade limitation",
        "",
        "Bastillion is redistributed as Loophole's official unmodified shaded JAR. Maven source",
        "resolution can reproduce release-version dependencies, but a dependency identified only as",
        "`*-SNAPSHOT` cannot by itself reveal the timestamped snapshot that was used when the already",
        "published shaded JAR was built. Such cases are listed as warnings below rather than silently",
        "treated as reproducible.",
        "",
        "## Warnings",
        "",
    ]
    report.extend([f"- {w}" for w in warnings] or ["- None."])
    report.extend(["", "## Validation", ""])
    if errors:
        report.append("**FAILED**")
        report.extend([f"- {e}" for e in errors])
    else:
        report.append("**PASSED** — no missing legal text or identified source-availability gap was detected by the collector.")
    report.append("")
    (out / "COMPLIANCE.md").write_text("\n".join(report), encoding="utf-8")

    # Stable file inventory with hashes; do not include this file itself.
    hashes: list[str] = []
    for path in sorted(p for p in out.rglob("*") if p.is_file() and p.name != "SHA256SUMS"):
        hashes.append(f"{sha256(path)}  {path.relative_to(out).as_posix()}")
    (out / "SHA256SUMS").write_text("\n".join(hashes) + "\n", encoding="utf-8")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    print(
        f"Compliance bundle complete: {len(maven_components)} Maven components, "
        f"{len(npm_components)} npm components."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
