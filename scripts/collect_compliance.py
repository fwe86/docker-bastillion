#!/usr/bin/env python3

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
import urllib.error
import urllib.request
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

# Canonical full-text fallbacks. Project-supplied legal files always take precedence.
# SPDX's license-list-data repository is used only when an artifact/source JAR does
# not itself carry the complete standard license text.
SPDX_ALIASES = {
    "apache 2.0": "Apache-2.0",
    "apache license 2.0": "Apache-2.0",
    "apache license, version 2.0": "Apache-2.0",
    "apache software license, version 2.0": "Apache-2.0",
    "the apache software license, version 2.0": "Apache-2.0",
    "apache-2.0": "Apache-2.0",
    "mit": "MIT",
    "mit license": "MIT",
    "bsd-3-clause": "BSD-3-Clause",
    "the 3-clause bsd license": "BSD-3-Clause",
    "3-clause bsd": "BSD-3-Clause",
    "new bsd license": "BSD-3-Clause",
    "bsd-2-clause": "BSD-2-Clause",
    "2-clause bsd": "BSD-2-Clause",
    "epl-2.0": "EPL-2.0",
    "eclipse public license 2.0": "EPL-2.0",
    "eclipse public license - v 2.0": "EPL-2.0",
    "eclipse public license - version 2.0": "EPL-2.0",
    "epl-1.0": "EPL-1.0",
    "eclipse public license 1.0": "EPL-1.0",
    "eclipse public license - v 1.0": "EPL-1.0",
    "eclipse public license - version 1.0": "EPL-1.0",
    "mpl 2.0": "MPL-2.0",
    "mpl-2.0": "MPL-2.0",
    "mozilla public license 2.0": "MPL-2.0",
    "mozilla public license, version 2.0": "MPL-2.0",
    "mpl 1.1": "MPL-1.1",
    "mpl-1.1": "MPL-1.1",
    "mozilla public license 1.1": "MPL-1.1",
    "lgpl 2.1": "LGPL-2.1-only",
    "lgpl-2.1": "LGPL-2.1-only",
    "gnu lesser general public license, version 2.1": "LGPL-2.1-only",
    "gpl 2.0": "GPL-2.0-only",
    "gpl-2.0": "GPL-2.0-only",
    "gnu general public license, version 2": "GPL-2.0-only",
    "cddl 1.1": "CDDL-1.1",
    "cddl-1.1": "CDDL-1.1",
    "common development and distribution license 1.1": "CDDL-1.1",
    "cddl 1.0": "CDDL-1.0",
    "cddl-1.0": "CDDL-1.0",
    "common development and distribution license 1.0": "CDDL-1.0",
    "classpath-exception-2.0": "Classpath-exception-2.0",
}


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
        components.append(MavenComponent(group, artifact, packaging, classifier, version, scope, artifact_path))
    if not components:
        raise ComplianceError(f"No Maven dependencies parsed from {path}")
    return sorted(components, key=lambda c: (c.group, c.artifact, c.version, c.classifier))


def find_repository_root(path: Path) -> Path | None:
    for parent in [path] + list(path.parents):
        if parent.name == "repository" and parent.parent.name == ".m2":
            return parent
    return None


def find_pom(component: MavenComponent) -> Path | None:
    parent = component.artifact_path.parent
    exact = parent / f"{component.artifact}-{component.version}.pom"
    if exact.is_file():
        return exact
    poms = sorted(parent.glob("*.pom"))
    return poms[0] if poms else None


def text_of(node: ET.Element | None, child: str) -> str:
    if node is None:
        return ""
    return node.findtext(f"{{*}}{child}", default="").strip()


def resolve_props(value: str, props: dict[str, str]) -> str:
    for _ in range(10):
        changed = False
        for key, replacement in props.items():
            token = "${" + key + "}"
            if token in value:
                value = value.replace(token, replacement)
                changed = True
        if not changed:
            break
    return value


def load_pom_chain(pom_path: Path | None, repo_root: Path | None) -> list[tuple[Path, ET.Element]]:
    if pom_path is None or not pom_path.is_file():
        return []
    result: list[tuple[Path, ET.Element]] = []
    seen: set[Path] = set()
    current = pom_path
    inherited_props: dict[str, str] = {}

    for _ in range(12):
        current = current.resolve()
        if current in seen or not current.is_file():
            break
        seen.add(current)
        try:
            root = ET.parse(current).getroot()
        except ET.ParseError:
            break
        result.append((current, root))

        project_version = text_of(root, "version") or text_of(root.find("./{*}parent"), "version")
        project_group = text_of(root, "groupId") or text_of(root.find("./{*}parent"), "groupId")
        project_artifact = text_of(root, "artifactId")
        props = dict(inherited_props)
        props.update({
            "project.version": project_version,
            "pom.version": project_version,
            "project.groupId": project_group,
            "pom.groupId": project_group,
            "project.artifactId": project_artifact,
            "pom.artifactId": project_artifact,
        })
        properties = root.find("./{*}properties")
        if properties is not None:
            for child in list(properties):
                key = child.tag.split("}")[-1]
                props[key] = (child.text or "").strip()
        inherited_props = props

        parent = root.find("./{*}parent")
        if parent is None or repo_root is None:
            break
        pg = resolve_props(text_of(parent, "groupId"), props)
        pa = resolve_props(text_of(parent, "artifactId"), props)
        pv = resolve_props(text_of(parent, "version"), props)
        if not (pg and pa and pv) or "${" in pg + pa + pv:
            break
        candidate = repo_root.joinpath(*pg.split("."), pa, pv, f"{pa}-{pv}.pom")
        if not candidate.is_file():
            break
        current = candidate
    return result


def pom_metadata(pom_path: Path | None, repo_root: Path | None) -> tuple[list[str], list[str], str, list[str], list[Path]]:
    chain = load_pom_chain(pom_path, repo_root)
    names: list[str] = []
    urls: list[str] = []
    project_url = ""
    scm_values: list[str] = []

    for _, root in chain:
        if not names:
            for license_node in root.findall("./{*}licenses/{*}license"):
                name = license_node.findtext("{*}name", default="").strip()
                url = license_node.findtext("{*}url", default="").strip()
                if name:
                    names.append(name)
                if url:
                    urls.append(url)
        if not project_url:
            project_url = root.findtext("./{*}url", default="").strip()
        if not scm_values:
            scm = root.find("./{*}scm")
            if scm is not None:
                for child_name in ("url", "connection", "developerConnection", "tag"):
                    value = scm.findtext(f"{{*}}{child_name}", default="").strip()
                    if value:
                        scm_values.append(value)

    return sorted(set(names)), sorted(set(urls)), project_url, sorted(set(scm_values)), [p for p, _ in chain]


def manifest_license_metadata(jar: Path) -> tuple[list[str], list[str]]:
    names: list[str] = []
    urls: list[str] = []
    if not zipfile.is_zipfile(jar):
        return names, urls
    with zipfile.ZipFile(jar) as archive:
        try:
            raw = archive.read("META-INF/MANIFEST.MF").decode("utf-8", errors="replace")
        except KeyError:
            return names, urls
    # unfold continuation lines
    unfolded = re.sub(r"\r?\n ", "", raw)
    for line in unfolded.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if key in {"bundle-license", "spdx-license-identifier", "license", "implementation-license"} and value:
            for token in re.split(r"\s+(?:OR|AND)\s+|,", value):
                token = token.strip()
                if not token:
                    continue
                if token.startswith("http://") or token.startswith("https://"):
                    urls.append(token)
                else:
                    names.append(token)
    return sorted(set(names)), sorted(set(urls))


def source_jar_for(component: MavenComponent, source_root: Path) -> Path | None:
    # First check the repository beside the binary artifact. This also covers
    # components discovered only from the already-shaded Bastillion JAR.
    adjacent = component.artifact_path.parent / f"{component.artifact}-{component.version}-sources.jar"
    if adjacent.is_file():
        return adjacent

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


def normalized_license_name(value: str) -> str:
    value = re.sub(r"\s+", " ", value.strip().lower())
    value = value.replace("the ", "", 1) if value.startswith("the ") else value
    return value


def license_ids(names: list[str]) -> list[str]:
    result: set[str] = set()
    for name in names:
        norm = normalized_license_name(name)
        if norm in SPDX_ALIASES:
            result.add(SPDX_ALIASES[norm])
            continue
        # Accept already-valid common SPDX identifiers from manifests/POMs.
        if re.fullmatch(r"[A-Za-z0-9.+-]+", name) and any(
            token in name.upper() for token in ("MIT", "BSD", "APACHE", "MPL", "EPL", "GPL", "LGPL", "CDDL")
        ):
            result.add(name)
    return sorted(result)


def fetch_url(url: str, destination: Path) -> bool:
    if url.startswith("http://"):
        url = "https://" + url[len("http://"):]
    request = urllib.request.Request(url, headers={"User-Agent": "docker-bastillion-license-compliance/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            data = response.read(2_500_000)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return False
    if len(data) < 100:
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return True


def materialize_canonical_licenses(names: list[str], destination: Path) -> list[str]:
    copied: list[str] = []
    for spdx_id in license_ids(names):
        target = destination / f"{clean_segment(spdx_id)}.txt"
        url = f"https://raw.githubusercontent.com/spdx/license-list-data/main/text/{spdx_id}.txt"
        if fetch_url(url, target):
            copied.append(target.name)
    return copied


def materialize_declared_license_urls(urls: list[str], destination: Path) -> list[str]:
    copied: list[str] = []
    for index, url in enumerate(urls, start=1):
        target = destination / f"declared-license-{index}.txt"
        if fetch_url(url, target):
            copied.append(target.name)
    return copied


def looks_like_full_permissive_notice(text: str) -> bool:
    lower = text.lower()
    return (
        ("permission is hereby granted" in lower and "copyright" in lower)
        or ("redistribution and use in source and binary forms" in lower and "copyright" in lower)
    )


def extract_copyright_evidence(pom_chain: list[Path], source_jar: Path | None, destination: Path) -> int:
    evidence: set[str] = set()

    for pom in pom_chain:
        try:
            text = pom.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line in text.splitlines():
            if "copyright" in line.lower():
                cleaned = re.sub(r"^[\s*#/<!>-]+", "", line).strip()
                if cleaned:
                    evidence.add(cleaned)

    if source_jar and zipfile.is_zipfile(source_jar):
        with zipfile.ZipFile(source_jar) as archive:
            inspected = 0
            for info in archive.infolist():
                if info.is_dir() or info.file_size > 500_000:
                    continue
                suffix = PurePosixPath(info.filename).suffix.lower()
                if suffix not in {".java", ".kt", ".scala", ".xml", ".txt", ".properties", ".md"}:
                    continue
                try:
                    text = archive.read(info).decode("utf-8", errors="ignore")[:12000]
                except Exception:
                    continue
                inspected += 1
                for line in text.splitlines():
                    if "copyright" in line.lower():
                        cleaned = re.sub(r"^[\s*#/<!>-]+", "", line).strip()
                        if cleaned:
                            evidence.add(cleaned)
                if inspected >= 250:
                    break

    if evidence:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("\n".join(sorted(evidence)) + "\n", encoding="utf-8")
    return len(evidence)




def infer_license_names_from_poms(pom_chain: list[Path]) -> list[str]:
    text = "\n".join(
        p.read_text(encoding="utf-8", errors="ignore")
        for p in pom_chain
        if p.is_file()
    ).lower()
    result: set[str] = set()
    if "apache license" in text and "2.0" in text:
        result.add("Apache-2.0")
    if "permission is hereby granted" in text:
        result.add("MIT")
    if "redistribution" in text and "source and binary" in text and "neither" in text:
        result.add("BSD-3-Clause")
    if "mozilla public license" in text and ("2.0" in text or "version 2" in text):
        result.add("MPL-2.0")
    if "mozilla public license" in text and ("1.1" in text or "version 1.1" in text):
        result.add("MPL-1.1")
    if "eclipse public license" in text and ("2.0" in text or "version 2" in text):
        result.add("EPL-2.0")
    if "eclipse public license" in text and ("1.0" in text or "version 1" in text):
        result.add("EPL-1.0")
    if "common development and distribution license" in text or "cddl" in text:
        result.add("CDDL-1.1")
    if "general public license version 2" in text or "gpl version 2" in text:
        result.add("GPL-2.0-only")
    if "classpath exception" in text:
        result.add("Classpath-exception-2.0")
    return sorted(result)


def extract_full_source_license_headers(source_jar: Path | None, destination: Path) -> int:
    if source_jar is None or not zipfile.is_zipfile(source_jar):
        return 0
    blocks: set[str] = set()
    with zipfile.ZipFile(source_jar) as archive:
        inspected = 0
        for info in archive.infolist():
            if info.is_dir() or info.file_size > 500_000:
                continue
            suffix = PurePosixPath(info.filename).suffix.lower()
            if suffix not in {".java", ".kt", ".scala", ".xml", ".txt", ".properties", ".md"}:
                continue
            try:
                text = archive.read(info).decode("utf-8", errors="ignore")[:16000]
            except Exception:
                continue
            inspected += 1
            lower = text.lower()
            if ("permission is hereby granted" in lower and "copyright" in lower) or (
                "redistribution" in lower and "source and binary" in lower and "copyright" in lower
            ):
                header_lines: list[str] = []
                for line in text.splitlines()[:140]:
                    stripped = line.strip()
                    if re.match(r"^(package|import)\s+", stripped):
                        break
                    header_lines.append(line)
                block = "\n".join(header_lines).strip()
                if block:
                    blocks.add(block)
            if inspected >= 300:
                break
    if blocks:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(("\n\n----- SOURCE LICENSE HEADER -----\n\n").join(sorted(blocks)) + "\n", encoding="utf-8")
    return len(blocks)

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
        name = lock_path[len("node_modules/"):]
        version = str(meta.get("version", "")).strip()
        if not name or not version:
            raise ComplianceError(f"Incomplete npm package metadata for {lock_path}")
        package_dir = node_modules / name
        if not package_dir.is_dir():
            raise ComplianceError(f"npm package directory missing: {package_dir}")
        result.append(NpmComponent(name, version, package_dir, str(meta.get("resolved", "")), str(meta.get("integrity", ""))))
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
            "The upstream JAR contains Maven coordinates that were not materialized for compliance: "
            + ", ".join(":".join(c) for c in unexpected_embedded)
        )

    for component in maven_components:
        component_dir = out / "maven" / clean_segment(component.group) / clean_segment(component.artifact) / clean_segment(component.version)
        component_dir.mkdir(parents=True, exist_ok=True)

        pom = find_pom(component)
        repo_root = find_repository_root(component.artifact_path)
        license_names, license_urls, project_url, scm_values, pom_chain = pom_metadata(pom, repo_root)
        manifest_names, manifest_urls = manifest_license_metadata(component.artifact_path)
        if not license_names:
            license_names = manifest_names
        else:
            license_names = sorted(set(license_names + manifest_names))
        license_urls = sorted(set(license_urls + manifest_urls))
        if not license_names:
            license_names = infer_license_names_from_poms(pom_chain)

        if pom:
            shutil.copy2(pom, component_dir / "pom.xml")
        if len(pom_chain) > 1:
            parents = component_dir / "pom-parents"
            parents.mkdir(parents=True, exist_ok=True)
            for idx, parent_pom in enumerate(pom_chain[1:], start=1):
                shutil.copy2(parent_pom, parents / f"{idx:02d}-{parent_pom.name}")

        legal_dir = component_dir / "legal"
        project_legal = copy_legal_files_from_zip(component.artifact_path, legal_dir / "binary-artifact")

        source_jar = source_jar_for(component, args.maven_sources)
        source_rel = ""
        if source_jar:
            source_copy = component_dir / "source" / source_jar.name
            source_copy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_jar, source_copy)
            source_rel = source_copy.relative_to(out).as_posix()
            project_legal += copy_legal_files_from_zip(source_jar, legal_dir / "source-artifact")

        # Some projects publish the complete BSD/MIT notice in the POM header rather
        # than inside the binary/source JAR. Preserve that exact POM as legal evidence.
        if pom and looks_like_full_permissive_notice(pom.read_text(encoding="utf-8", errors="ignore")):
            target = legal_dir / "project-pom-with-license-notice.xml"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(pom, target)
            project_legal.append(target.relative_to(legal_dir).as_posix())

        source_header_count = extract_full_source_license_headers(
            source_jar,
            legal_dir / "SOURCE-LICENSE-HEADERS.txt",
        )
        if source_header_count:
            project_legal.append("SOURCE-LICENSE-HEADERS.txt")

        canonical = materialize_canonical_licenses(license_names, legal_dir / "canonical-license-texts")
        declared_url_copies: list[str] = []
        # A POM may identify a license that is not covered by our SPDX alias map.
        # In that case preserve the publisher-declared license URL as a fallback.
        if not canonical and license_urls:
            declared_url_copies = materialize_declared_license_urls(license_urls, legal_dir / "declared-license-texts")

        copyright_count = extract_copyright_evidence(
            pom_chain,
            source_jar,
            legal_dir / "COPYRIGHT-EVIDENCE.txt",
        )

        legal_paths = [p for p in legal_dir.rglob("*") if p.is_file()]
        evidence_text = " ".join(license_names + license_urls) + "\n" + read_small_text_files(legal_paths)
        source_required = any(pattern in evidence_text.lower() for pattern in SOURCE_REQUIRED_PATTERNS)

        if not legal_paths:
            errors.append(f"No full legal text/notice could be materialized for Maven component {component.coordinate}.")
        if not license_names and not project_legal:
            errors.append(f"No license identity could be established for Maven component {component.coordinate}.")
        if source_required and not source_jar:
            errors.append(f"Source availability could not be materialized for source-requiring Maven component {component.coordinate}.")

        ids = license_ids(license_names)
        if any(i == "MIT" or i.startswith("BSD-") for i in ids) and not project_legal and copyright_count == 0:
            errors.append(
                f"No project-specific copyright notice was found for permissively licensed Maven component {component.coordinate}."
            )

        if "SNAPSHOT" in component.version.upper():
            warnings.append(
                f"{component.coordinate} is a SNAPSHOT dependency. Its generic Maven version does not identify the timestamped build used when Loophole created the already-shaded release JAR. The official Bastillion release JAR SHA-256 remains the authoritative binary identity."
            )

        rows.append({
            "ecosystem": "maven",
            "name": f"{component.group}:{component.artifact}",
            "version": component.version,
            "declared_license": " OR ".join(license_names),
            "license_urls": " ".join(license_urls),
            "artifact_sha256": sha256(component.artifact_path),
            "legal_files": str(len(legal_paths)),
            "source_materialized": "yes" if source_jar else "no",
            "source_path_or_url": source_rel or project_url or " ".join(scm_values),
        })

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
        rows.append({
            "ecosystem": "npm",
            "name": component.name,
            "version": component.version,
            "declared_license": license_text,
            "license_urls": "",
            "artifact_sha256": component.integrity,
            "legal_files": str(len(legal_files)),
            "source_materialized": "no",
            "source_path_or_url": component.resolved or repository or homepage,
        })

    fieldnames = [
        "ecosystem", "name", "version", "declared_license", "license_urls",
        "artifact_sha256", "legal_files", "source_materialized", "source_path_or_url",
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
        "For Maven artifacts that omit a complete standard license text from their JARs, the",
        "collector preserves POM/manifest license identity and materializes the corresponding",
        "canonical SPDX license text. Project-specific LICENSE/NOTICE/COPYRIGHT files and source",
        "copyright evidence remain preserved separately and take precedence over that fallback.",
        "",
        f"Maven runtime/shaded components collected: **{len(maven_components)}**  ",
        f"npm components collected: **{len(npm_components)}**  ",
        f"Legal resources surviving inside the upstream shaded JAR: **{len(upstream_jar_files)}**",
        "",
        "## Source availability",
        "",
        "Where Maven source JARs are published, they are included below each component under",
        "`maven/.../source/`. This intentionally includes more source material than is required",
        "for many permissively licensed components and prevents identified MPL/EPL/GPL/LGPL/CDDL",
        "source-availability obligations from being left to a bare external URL.",
        "",
        "For npm components, `COMPONENTS.tsv` records the integrity value and registry tarball",
        "URL from the exact upstream lock file. Full license/notice files from the installed",
        "package are retained under `npm/.../legal/`.",
        "",
        "## Upstream shade limitation",
        "",
        "Bastillion is redistributed as Loophole's official unmodified shaded JAR. Components",
        "whose Maven metadata survives inside that JAR are independently materialized even if",
        "they are absent from the current dependency:list output. A dependency identified only",
        "as `*-SNAPSHOT` cannot by itself reveal the timestamped snapshot used when the already",
        "published shaded JAR was built; such cases are explicitly reported as warnings.",
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
        report.append("**PASSED** — no missing legal text, unmatched shaded Maven component, or identified source-availability gap was detected by the collector.")
    report.append("")
    (out / "COMPLIANCE.md").write_text("\n".join(report), encoding="utf-8")

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
    print(f"Compliance bundle complete: {len(maven_components)} Maven components, {len(npm_components)} npm components.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ComplianceError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
