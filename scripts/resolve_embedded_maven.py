#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath


def parse_existing(path: Path) -> set[tuple[str, str, str]]:
    result: set[tuple[str, str, str]] = set()
    if not path.is_file():
        return result
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if " -- " in line:
            line = line.split(" -- ", 1)[0].rstrip()
        parts = line.split(":")
        if len(parts) < 6:
            continue
        artifact_path = Path(parts[-1])
        scope = parts[-2]
        if not artifact_path.is_absolute() or scope not in {"compile", "runtime", "provided", "system", "test", "import"}:
            continue
        result.add((parts[0], parts[1], parts[-3]))
    return result


def embedded_coordinates(jar: Path) -> set[tuple[str, str, str]]:
    coords: set[tuple[str, str, str]] = set()
    with zipfile.ZipFile(jar) as archive:
        for info in archive.infolist():
            p = PurePosixPath(info.filename)
            if p.name != "pom.properties" or "META-INF" not in p.parts or "maven" not in p.parts:
                continue
            values: dict[str, str] = {}
            for raw in archive.read(info).decode("utf-8", errors="replace").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
            group = values.get("groupId", "")
            artifact = values.get("artifactId", "")
            version = values.get("version", "")
            if group and artifact and version:
                coords.add((group, artifact, version))
    return coords


def run_maven(artifact: str, plugin_version: str, *, classifier: str | None = None, fail: bool = True) -> bool:
    coordinate = artifact if classifier is None else f"{artifact}:jar:{classifier}"
    cmd = [
        "mvn",
        "--batch-mode",
        "--no-transfer-progress",
        f"org.apache.maven.plugins:maven-dependency-plugin:{plugin_version}:get",
        f"-Dartifact={coordinate}",
        "-Dtransitive=false",
    ]
    completed = subprocess.run(cmd, check=False)
    if completed.returncode != 0 and fail:
        raise RuntimeError(f"Maven could not resolve {coordinate}")
    return completed.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jar", required=True, type=Path)
    parser.add_argument("--maven-list", required=True, type=Path)
    parser.add_argument("--plugin-version", required=True)
    args = parser.parse_args()

    existing = parse_existing(args.maven_list)
    embedded = embedded_coordinates(args.jar)

    missing = sorted(
        coord
        for coord in embedded
        if coord not in existing and not (coord[0] == "io.bastillion" and coord[1] == "bastillion")
    )

    if not missing:
        print("No additional Maven coordinates found only inside the shaded JAR.")
        return 0

    repo = Path.home() / ".m2" / "repository"
    appended: list[str] = []

    for group, artifact, version in missing:
        gav = f"{group}:{artifact}:{version}"
        print(f"Resolving shaded-JAR-only component: {gav}")
        run_maven(gav, args.plugin_version)
        run_maven(gav, args.plugin_version, classifier="sources", fail=False)

        base = repo.joinpath(*group.split("."), artifact, version)
        jar = base / f"{artifact}-{version}.jar"
        if not jar.is_file():
            candidates = sorted(p for p in base.glob("*.jar") if not p.name.endswith("-sources.jar") and not p.name.endswith("-javadoc.jar"))
            if len(candidates) != 1:
                raise RuntimeError(f"Could not identify binary JAR for {gav} in {base}")
            jar = candidates[0]

        appended.append(f"{group}:{artifact}:jar:{version}:runtime:{jar.resolve()}")

    with args.maven_list.open("a", encoding="utf-8") as f:
        for line in appended:
            f.write(line + "\n")

    print(f"Added {len(appended)} shaded-JAR-only Maven component(s) to the compliance input.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
