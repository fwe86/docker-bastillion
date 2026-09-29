#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path


class ComplianceError(RuntimeError):
    pass


def run(cmd, *, cwd=None, capture=False, input_text=None):
    result = subprocess.run(
        cmd,
        cwd=cwd,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        check=False,
    )
    if result.returncode != 0:
        detail = ""
        if capture:
            detail = f"\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        raise ComplianceError(f"Command failed ({result.returncode}): {' '.join(cmd)}{detail}")
    return result.stdout if capture else ""


def docker_text(image_ref: str, platform: str, script: str) -> str:
    return run(
        [
            "docker", "run", "--rm", f"--platform={platform}",
            "--entrypoint", "/bin/sh", image_ref, "-c", script,
        ],
        capture=True,
    )


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_segment(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._+-]+", "_", value).strip("._") or "unknown"


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    run([
        "curl", "--fail", "--silent", "--show-error", "--location",
        "--retry", "5", "--retry-all-errors", url,
        "--output", str(destination),
    ])


def parse_dsc(path: Path) -> tuple[str, str, list[tuple[str, str]]]:
    source = ""
    version = ""
    checksums: list[tuple[str, str]] = []
    in_sha256 = False

    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if raw.startswith("Source:") and not source:
            source = raw.split(":", 1)[1].strip().split()[0]
        elif raw.startswith("Version:") and not version:
            version = raw.split(":", 1)[1].strip()

        if raw == "Checksums-Sha256:":
            in_sha256 = True
            continue
        if in_sha256:
            if not raw.startswith(" "):
                in_sha256 = False
                continue
            parts = raw.split()
            if len(parts) == 3 and re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]):
                checksums.append((parts[2], parts[0].lower()))

    if not source or not version:
        raise ComplianceError(f"Unable to parse Source/Version from {path}")
    if not checksums:
        raise ComplianceError(f"No Checksums-Sha256 section found in {path}")
    return source, version, checksums


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Materialize exact source code and evidence for a pinned Eclipse Temurin Ubuntu base image."
    )
    parser.add_argument("--base-image-ref", required=True)
    parser.add_argument("--base-image-name", required=True)
    parser.add_argument("--base-image-digest", required=True)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    if not re.fullmatch(r"sha256:[0-9a-f]{64}", args.base_image_digest):
        raise ComplianceError("Base image digest is not a valid sha256 digest")

    if shutil.which("docker") is None:
        raise ComplianceError("docker is required")
    if shutil.which("pull-lp-source") is None:
        raise ComplianceError("pull-lp-source is required (ubuntu-dev-tools package)")
    if shutil.which("curl") is None:
        raise ComplianceError("curl is required")

    out = args.output.resolve()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    shutil.copy2(args.manifest, out / "BASE-IMAGE-MANIFEST.json")

    platforms = {
        "amd64": "linux/amd64",
        "arm64": "linux/arm64",
    }

    # A multi-platform digest identifies the OCI/Docker image index, not one
    # concrete platform image. Docker Engine may cache the first platform under
    # that index digest and then refuse to overwrite the same digest when a
    # second platform is requested. Resolve and run each platform by its own
    # immutable child-manifest digest instead. The index digest remains the
    # canonical base-image identity used by BuildKit for the multi-platform build.
    try:
        manifest_doc = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ComplianceError(f"Unable to parse base-image manifest JSON: {exc}") from exc

    manifest_digest = str(manifest_doc.get("digest", ""))
    if manifest_digest != args.base_image_digest:
        raise ComplianceError(
            f"Base-image manifest digest mismatch: expected {args.base_image_digest}, "
            f"got {manifest_digest or 'missing'}"
        )

    descriptors = manifest_doc.get("manifests")
    if not isinstance(descriptors, list):
        raise ComplianceError("Base-image manifest does not contain a manifests array")

    platform_refs: dict[str, str] = {}
    platform_digests: dict[str, str] = {}
    for arch, platform in platforms.items():
        os_name, arch_name = platform.split("/", 1)
        matches = [
            item for item in descriptors
            if isinstance(item, dict)
            and isinstance(item.get("platform"), dict)
            and item["platform"].get("os") == os_name
            and item["platform"].get("architecture") == arch_name
        ]
        if len(matches) != 1:
            raise ComplianceError(
                f"Expected exactly one manifest descriptor for {platform}, found {len(matches)}"
            )
        digest = str(matches[0].get("digest", ""))
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
            raise ComplianceError(f"Invalid child-manifest digest for {platform}: {digest!r}")
        platform_digests[arch] = digest
        platform_refs[arch] = f"{args.base_image_name}@{digest}"

    source_tuples: set[tuple[str, str]] = set()
    java_versions: set[str] = set()

    inventory_dir = out / "inventory"
    legal_dir = out / "legal-evidence"
    adoptium_dir = out / "adoptium-container"
    inventory_dir.mkdir()
    legal_dir.mkdir()
    adoptium_dir.mkdir()

    with (inventory_dir / "PLATFORM-MANIFESTS.tsv").open("w", encoding="utf-8", newline="") as f:
        f.write("architecture\tplatform\tindex_digest\tplatform_digest\tpinned_reference\n")
        for arch, platform in platforms.items():
            f.write(
                f"{arch}\t{platform}\t{args.base_image_digest}\t"
                f"{platform_digests[arch]}\t{platform_refs[arch]}\n"
            )

    query = (
        "dpkg-query -W -f='${binary:Package}\\t${Package}\\t${Version}\\t"
        "${source:Package}\\t${source:Version}\\n'"
    )

    for arch, platform in platforms.items():
        platform_ref = platform_refs[arch]
        raw_inventory = docker_text(platform_ref, platform, query)
        rows: list[tuple[str, str, str, str, str]] = []
        for line in raw_inventory.splitlines():
            fields = line.split("\t")
            if len(fields) != 5:
                raise ComplianceError(f"Unexpected dpkg-query row for {arch}: {line!r}")
            binary_pkg, package, binary_version, source_pkg, source_version = fields
            source_pkg = source_pkg.strip() or package.strip()
            source_version = source_version.strip() or binary_version.strip()
            if not all([binary_pkg.strip(), package.strip(), binary_version.strip(), source_pkg, source_version]):
                raise ComplianceError(f"Incomplete package metadata for {arch}: {line!r}")
            rows.append((binary_pkg.strip(), binary_version.strip(), source_pkg, source_version, arch))
            source_tuples.add((source_pkg, source_version))

        rows.sort(key=lambda r: (r[0], r[1]))
        inv_path = inventory_dir / f"DPKG-PACKAGES-{arch}.tsv"
        with inv_path.open("w", encoding="utf-8", newline="") as f:
            f.write("binary_package\tbinary_version\tsource_package\tsource_version\tarchitecture\n")
            for row in rows:
                f.write("\t".join(row) + "\n")

        java_version = docker_text(platform_ref, platform, "printf '%s\\n' \"${JAVA_VERSION:?JAVA_VERSION is not set}\"").strip()
        if not re.fullmatch(r"jdk-[0-9][0-9A-Za-z.+_-]*", java_version):
            raise ComplianceError(f"Unexpected JAVA_VERSION for {arch}: {java_version!r}")
        java_versions.add(java_version)
        (inventory_dir / f"JAVA-VERSION-{arch}.txt").write_text(java_version + "\n", encoding="utf-8")

        release_text = docker_text(
            platform_ref,
            platform,
            "cat /opt/java/openjdk/release",
        )
        (inventory_dir / f"OPENJDK-RELEASE-{arch}.txt").write_text(release_text, encoding="utf-8")

        legal_hashes = docker_text(
            platform_ref,
            platform,
            r'''set -eu
cd /
{
  find usr/share/doc -maxdepth 2 \( -type f -o -type l \) -name copyright -print0 2>/dev/null || true
  find opt/java/openjdk/legal -type f -print0 2>/dev/null || true
} | sort -z | xargs -0 -r sha256sum
''',
        )
        if not legal_hashes.strip():
            raise ComplianceError(f"No base-image legal files discovered for {arch}")
        (legal_dir / f"LEGAL-FILES-SHA256-{arch}.txt").write_text(legal_hashes, encoding="utf-8")

        entrypoint = docker_text(platform_ref, platform, "cat /__cacert_entrypoint.sh")
        if "Apache License, Version 2.0" not in entrypoint:
            raise ComplianceError(f"Adoptium entrypoint for {arch} lacks expected Apache-2.0 notice")
        (adoptium_dir / f"__cacert_entrypoint-{arch}.sh").write_text(entrypoint, encoding="utf-8")

    if len(java_versions) != 1:
        raise ComplianceError(f"Temurin JAVA_VERSION differs between target architectures: {sorted(java_versions)}")

    java_version = next(iter(java_versions))
    major_match = re.match(r"jdk-(\d+)", java_version)
    if not major_match:
        raise ComplianceError(f"Cannot derive JDK major from {java_version}")
    jdk_major = major_match.group(1)
    source_version = java_version.removeprefix("jdk-").replace("+", "_")
    release_tag = urllib.parse.quote(java_version, safe="")
    temurin_filename = f"OpenJDK{jdk_major}U-jdk-sources_{source_version}.tar.gz"
    temurin_base = (
        f"https://github.com/adoptium/temurin{jdk_major}-binaries/releases/download/"
        f"{release_tag}/{temurin_filename}"
    )

    temurin_dir = out / "temurin"
    temurin_dir.mkdir()
    temurin_path = temurin_dir / temurin_filename
    checksum_path = temurin_dir / f"{temurin_filename}.sha256.txt"
    signature_path = temurin_dir / f"{temurin_filename}.sig"

    download(temurin_base, temurin_path)
    download(temurin_base + ".sha256.txt", checksum_path)
    download(temurin_base + ".sig", signature_path)

    checksum_text = checksum_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"\b([0-9a-fA-F]{64})\b", checksum_text)
    if not match:
        raise ComplianceError(f"No SHA-256 found in {checksum_path}")
    expected_temurin_sha = match.group(1).lower()
    actual_temurin_sha = sha256(temurin_path)
    if actual_temurin_sha != expected_temurin_sha:
        raise ComplianceError(
            f"Temurin source SHA-256 mismatch: expected {expected_temurin_sha}, got {actual_temurin_sha}"
        )

    # Preserve Adoptium's own release metadata for the exact source archive and
    # for each JRE architecture. Besides identifying the released binary, this
    # metadata records the exact temurin-build commit and the build arguments
    # used to create the release. We mirror the build-script source at every
    # exact commit referenced by those metadata files.
    source_metadata_path = temurin_dir / f"{temurin_filename}.json"
    download(temurin_base + ".json", source_metadata_path)
    try:
        source_metadata = json.loads(source_metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ComplianceError(f"Invalid Temurin source metadata JSON: {exc}") from exc

    if source_metadata.get("binary_type") != "sources":
        raise ComplianceError("Temurin source metadata does not describe a sources artifact")
    if str(source_metadata.get("sha256", "")).lower() != actual_temurin_sha:
        raise ComplianceError("Temurin source metadata SHA-256 does not match the downloaded source archive")

    expected_release_version = java_version.removeprefix("jdk-")
    metadata_version = str(source_metadata.get("version", {}).get("version", ""))
    if not metadata_version.startswith(expected_release_version):
        raise ComplianceError(
            f"Temurin source metadata version {metadata_version!r} does not match {expected_release_version!r}"
        )

    metadata_dir = temurin_dir / "release-metadata"
    metadata_dir.mkdir()
    shutil.copy2(source_metadata_path, metadata_dir / source_metadata_path.name)
    source_metadata_path.unlink()

    build_refs: dict[str, set[str]] = {}
    build_ref_pattern = re.compile(
        r"^https://github\.com/adoptium/temurin-build/commit/([0-9a-fA-F]{40})$"
    )

    def register_build_metadata(label: str, metadata: dict) -> None:
        vendor = str(metadata.get("vendor", ""))
        if vendor != "Eclipse Adoptium":
            raise ComplianceError(f"Unexpected Temurin metadata vendor for {label}: {vendor!r}")
        version_value = str(metadata.get("version", {}).get("version", ""))
        if not version_value.startswith(expected_release_version):
            raise ComplianceError(
                f"Temurin metadata version for {label} does not match runtime: {version_value!r}"
            )
        build_ref = str(metadata.get("buildRef", ""))
        m = build_ref_pattern.fullmatch(build_ref)
        if not m:
            raise ComplianceError(f"Temurin metadata for {label} lacks an exact temurin-build commit: {build_ref!r}")
        commit = m.group(1).lower()
        build_refs.setdefault(commit, set()).add(label)
        args_value = str(metadata.get("makejdk_any_platform_args", ""))
        scm_ref = str(metadata.get("scmRef", ""))
        if not args_value.strip() or not scm_ref.strip():
            raise ComplianceError(f"Temurin metadata for {label} lacks build arguments or scmRef")

    register_build_metadata("sources", source_metadata)

    temurin_arch_names = {"amd64": "x64", "arm64": "aarch64"}
    for arch, release_arch in temurin_arch_names.items():
        jre_filename = f"OpenJDK{jdk_major}U-jre_{release_arch}_linux_hotspot_{source_version}.tar.gz"
        jre_metadata_url = (
            f"https://github.com/adoptium/temurin{jdk_major}-binaries/releases/download/"
            f"{release_tag}/{jre_filename}.json"
        )
        jre_metadata_path = metadata_dir / f"{jre_filename}.json"
        download(jre_metadata_url, jre_metadata_path)
        try:
            jre_metadata = json.loads(jre_metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ComplianceError(f"Invalid Temurin JRE metadata JSON for {arch}: {exc}") from exc
        if jre_metadata.get("binary_type") != "jre":
            raise ComplianceError(f"Temurin metadata for {arch} does not describe a JRE")
        if str(jre_metadata.get("arch", "")) != release_arch:
            raise ComplianceError(f"Temurin metadata architecture mismatch for {arch}")
        register_build_metadata(arch, jre_metadata)

    build_scripts_dir = temurin_dir / "temurin-build"
    build_scripts_dir.mkdir()
    build_script_rows: list[tuple[str, str, str]] = []
    for commit, labels in sorted(build_refs.items()):
        archive_name = f"temurin-build-{commit}.tar.gz"
        archive_url = f"https://github.com/adoptium/temurin-build/archive/{commit}.tar.gz"
        archive_path = build_scripts_dir / archive_name
        download(archive_url, archive_path)
        archive_sha = sha256(archive_path)
        build_script_rows.append((commit, ",".join(sorted(labels)), archive_sha))

    with (temurin_dir / "BUILD-SCRIPTS.tsv").open("w", encoding="utf-8") as f:
        f.write("temurin_build_commit\tmetadata_roles\tarchive_sha256\n")
        for row in build_script_rows:
            f.write("\t".join(row) + "\n")

    (temurin_dir / "SOURCE-INFO.tsv").write_text(
        "java_version\tsource_url\tsha256\n"
        f"{java_version}\t{temurin_base}\t{actual_temurin_sha}\n",
        encoding="utf-8",
    )

    source_list_path = out / "SOURCE-PACKAGES.tsv"
    with source_list_path.open("w", encoding="utf-8") as f:
        f.write("source_package\tsource_version\n")
        for source_pkg, version in sorted(source_tuples):
            f.write(f"{source_pkg}\t{version}\n")

    ubuntu_dir = out / "ubuntu-sources"
    ubuntu_dir.mkdir()

    verified_sources: set[tuple[str, str]] = set()
    # Launchpad/archive downloads occasionally fail transiently (for example,
    # launchpadlibrarian timeouts).  A transient transport failure must not make
    # an otherwise compliant release impossible to publish, but we remain
    # fail-closed: after bounded retries the workflow still aborts and no image
    # is published.  Each retry starts from an empty component directory so a
    # partial prior download can never be mistaken for verified source.
    pull_attempts = 5
    retry_delays = (5, 15, 30, 60)

    for source_pkg, version in sorted(source_tuples):
        component_dir = ubuntu_dir / safe_segment(source_pkg) / safe_segment(version)
        last_error: ComplianceError | None = None

        for attempt in range(1, pull_attempts + 1):
            if component_dir.exists():
                shutil.rmtree(component_dir)
            component_dir.mkdir(parents=True)

            try:
                run(
                    ["pull-lp-source", "-d", "--no-conf", source_pkg, version],
                    cwd=component_dir,
                )
                last_error = None
                break
            except ComplianceError as exc:
                last_error = exc
                if attempt >= pull_attempts:
                    break
                delay = retry_delays[attempt - 1]
                print(
                    f"WARNING: source download failed for {source_pkg} {version} "
                    f"(attempt {attempt}/{pull_attempts}); retrying in {delay}s: {exc}",
                    file=sys.stderr,
                    flush=True,
                )
                time.sleep(delay)

        if last_error is not None:
            raise ComplianceError(
                f"Unable to download exact Ubuntu source package {source_pkg} {version} "
                f"after {pull_attempts} attempts: {last_error}"
            ) from last_error

        dsc_files = sorted(component_dir.glob("*.dsc"))
        if len(dsc_files) != 1:
            raise ComplianceError(
                f"Expected exactly one .dsc for {source_pkg} {version}, found {len(dsc_files)}"
            )

        got_source, got_version, checksums = parse_dsc(dsc_files[0])
        if got_source != source_pkg or got_version != version:
            raise ComplianceError(
                f"Source identity mismatch for {source_pkg} {version}: got {got_source} {got_version}"
            )

        for filename, expected in checksums:
            candidate = component_dir / filename
            if not candidate.is_file():
                raise ComplianceError(f"Source file listed by {dsc_files[0].name} is missing: {filename}")
            actual = sha256(candidate)
            if actual != expected:
                raise ComplianceError(
                    f"SHA-256 mismatch for {candidate}: expected {expected}, got {actual}"
                )
        verified_sources.add((source_pkg, version))

    missing = sorted(source_tuples - verified_sources)
    if missing:
        raise ComplianceError(f"Source packages not materialized: {missing}")

    readme = f"""# Base image corresponding source bundle

Base image: `{args.base_image_name}`
Pinned manifest digest: `{args.base_image_digest}`
Pinned multi-platform reference: `{args.base_image_ref}`
Target platforms: `linux/amd64`, `linux/arm64`
Platform-specific immutable manifest references are recorded in
`inventory/PLATFORM-MANIFESTS.tsv` and are used for all per-architecture
inspection commands.
Temurin runtime version: `{java_version}`
Ubuntu source package tuples materialized: {len(source_tuples)}

This bundle accompanies the published docker-bastillion image's pinned runtime
base. It contains the exact Ubuntu source package versions corresponding to all
installed Debian/Ubuntu binary packages observed in both target architectures,
and the exact Eclipse Temurin/OpenJDK source archive corresponding to the
runtime version in the pinned base image.

For Ubuntu packages, each directory contains the signed `.dsc` and every source
file referenced by its `Checksums-Sha256` section. The collector verifies those
SHA-256 values before publication. Ubuntu source packages are the source
material from which the corresponding binary packages are built.

For Eclipse Temurin/OpenJDK, the official release source archive is included and
verified against Adoptium's published SHA-256 file. The original signature file
and Adoptium release metadata are preserved as additional evidence. Those
metadata identify the exact `temurin-build` commit and build arguments used for
the release; the collector therefore also includes an archive of every exact
`temurin-build` commit referenced by the source/JRE metadata, covering the
build scripts used to control compilation and packaging.

`inventory/` records the exact binary-to-source package mapping for each target
architecture. `legal-evidence/` records hashes of the legal/copyright files that
remain in the pinned base image. `adoptium-container/` preserves the base
image's generated CA-certificate entrypoint script itself; that script carries
its Apache-2.0 notice and is source-form shell code.

Each source package remains governed by its own upstream license terms. This
bundle does not relicense any component.
"""
    (out / "README.md").write_text(readme, encoding="utf-8")

    hash_lines: list[str] = []
    for path in sorted(out.rglob("*")):
        if not path.is_file() or path.name == "SHA256SUMS":
            continue
        rel = path.relative_to(out).as_posix()
        hash_lines.append(f"{sha256(path)}  {rel}")
    (out / "SHA256SUMS").write_text("\n".join(hash_lines) + "\n", encoding="utf-8")

    print(
        f"Base image source bundle complete: {len(source_tuples)} Ubuntu source packages, "
        f"Temurin {java_version}."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ComplianceError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
