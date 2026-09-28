#!/usr/bin/env bash

set -euo pipefail

UPSTREAM_REPO="${UPSTREAM_REPO:-Loophole-LLC/Bastillion}"
REQUESTED_VERSION="${1:-latest}"
OUT_DIR="${OUT_DIR:-.build/upstream}"

API_BASE="https://api.github.com/repos/${UPSTREAM_REPO}"

mkdir -p "${OUT_DIR}"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

api_get() {
    local url="$1"

    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        curl \
            --fail \
            --silent \
            --show-error \
            --location \
            --header "Accept: application/vnd.github+json" \
            --header "Authorization: Bearer ${GITHUB_TOKEN}" \
            --header "X-GitHub-Api-Version: 2022-11-28" \
            --header "User-Agent: docker-bastillion" \
            "${url}"
    else
        curl \
            --fail \
            --silent \
            --show-error \
            --location \
            --header "Accept: application/vnd.github+json" \
            --header "X-GitHub-Api-Version: 2022-11-28" \
            --header "User-Agent: docker-bastillion" \
            "${url}"
    fi
}

if [[ "${REQUESTED_VERSION}" == "latest" ]]; then
    RELEASE_API_URL="${API_BASE}/releases/latest"
else
    TAG="${REQUESTED_VERSION}"

    if [[ "${TAG}" != v* ]]; then
        TAG="v${TAG}"
    fi

    RELEASE_API_URL="${API_BASE}/releases/tags/${TAG}"
fi

echo "Fetching release metadata from:"
echo "  ${RELEASE_API_URL}"

api_get "${RELEASE_API_URL}" > "${TMP_DIR}/release.json"

python3 - \
    "${TMP_DIR}/release.json" \
    "${TMP_DIR}/selected.json" \
    "${REQUESTED_VERSION}" <<'PY'
import json
import re
import sys

release_file = sys.argv[1]
output_file = sys.argv[2]
requested_version = sys.argv[3]

with open(release_file, "r", encoding="utf-8") as f:
    release = json.load(f)

if release.get("draft"):
    raise SystemExit("ERROR: Refusing to use a draft release.")

tag = release.get("tag_name")
if not tag:
    raise SystemExit("ERROR: Release does not contain tag_name.")

version = tag[1:] if tag.startswith("v") else tag
prerelease = bool(release.get("prerelease"))

if requested_version == "latest" and prerelease:
    raise SystemExit("ERROR: Latest release unexpectedly is a prerelease.")

expected_name = f"bastillion-{version}.jar"

assets = release.get("assets", [])
matches = [
    asset
    for asset in assets
    if asset.get("name") == expected_name
]

if len(matches) != 1:
    available = ", ".join(
        asset.get("name", "<unnamed>")
        for asset in assets
    )

    raise SystemExit(
        "ERROR: Expected exactly one release asset named "
        f"{expected_name!r}, found {len(matches)}.\n"
        f"Available assets: {available}"
    )

asset = matches[0]

digest = asset.get("digest")
if not digest:
    raise SystemExit(
        f"ERROR: Release asset {expected_name!r} has no digest."
    )

match = re.fullmatch(r"sha256:([0-9a-fA-F]{64})", digest)
if not match:
    raise SystemExit(
        f"ERROR: Unsupported or invalid digest: {digest!r}"
    )

download_url = asset.get("browser_download_url")
if not download_url:
    raise SystemExit(
        f"ERROR: Release asset {expected_name!r} has no download URL."
    )

selected = {
    "tag": tag,
    "version": version,
    "name": expected_name,
    "sha256": match.group(1).lower(),
    "download_url": download_url,
    "prerelease": prerelease,
    "published_at": release.get("published_at", ""),
    "release_url": release.get("html_url", ""),
}

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(selected, f, indent=2)
    f.write("\n")
PY

get_metadata() {
    local field="$1"

    python3 - "${TMP_DIR}/selected.json" "${field}" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    data = json.load(f)

value = data[sys.argv[2]]

if isinstance(value, bool):
    print("true" if value else "false")
else:
    print(value)
PY
}

TAG="$(get_metadata tag)"
VERSION="$(get_metadata version)"
JAR_NAME="$(get_metadata name)"
EXPECTED_SHA256="$(get_metadata sha256)"
JAR_URL="$(get_metadata download_url)"
PRERELEASE="$(get_metadata prerelease)"
PUBLISHED_AT="$(get_metadata published_at)"
RELEASE_URL="$(get_metadata release_url)"

echo
echo "Selected Bastillion release:"
echo "  tag:        ${TAG}"
echo "  version:    ${VERSION}"
echo "  prerelease: ${PRERELEASE}"
echo "  asset:      ${JAR_NAME}"
echo "  sha256:     ${EXPECTED_SHA256}"
echo

echo "Downloading ${JAR_NAME}..."

curl \
    --fail \
    --silent \
    --show-error \
    --location \
    "${JAR_URL}" \
    --output "${TMP_DIR}/bastillion.jar"

if command -v sha256sum >/dev/null 2>&1; then
    ACTUAL_SHA256="$(
        sha256sum "${TMP_DIR}/bastillion.jar" |
        awk '{print $1}'
    )"
elif command -v shasum >/dev/null 2>&1; then
    ACTUAL_SHA256="$(
        shasum -a 256 "${TMP_DIR}/bastillion.jar" |
        awk '{print $1}'
    )"
else
    echo "ERROR: Neither sha256sum nor shasum is available." >&2
    exit 1
fi

if [[ "${ACTUAL_SHA256}" != "${EXPECTED_SHA256}" ]]; then
    echo "ERROR: SHA-256 verification failed." >&2
    echo "Expected: ${EXPECTED_SHA256}" >&2
    echo "Actual:   ${ACTUAL_SHA256}" >&2
    exit 1
fi

echo "SHA-256 verification successful."

RAW_BASE="https://raw.githubusercontent.com/${UPSTREAM_REPO}/${TAG}"

echo
echo "Downloading upstream license information..."

curl \
    --fail \
    --silent \
    --show-error \
    --location \
    "${RAW_BASE}/LICENSE.md" \
    --output "${TMP_DIR}/LICENSE.md"

curl \
    --fail \
    --silent \
    --show-error \
    --location \
    "${RAW_BASE}/3rdPartyLicenses.md" \
    --output "${TMP_DIR}/3rdPartyLicenses.md"

rm -rf "${OUT_DIR}"
mkdir -p "${OUT_DIR}"

mv "${TMP_DIR}/bastillion.jar" \
   "${OUT_DIR}/bastillion.jar"

mv "${TMP_DIR}/LICENSE.md" \
   "${OUT_DIR}/LICENSE.md"

mv "${TMP_DIR}/3rdPartyLicenses.md" \
   "${OUT_DIR}/3rdPartyLicenses.md"

cp "${TMP_DIR}/release.json" \
   "${OUT_DIR}/release.json"

cp "${TMP_DIR}/selected.json" \
   "${OUT_DIR}/selected.json"

cat > "${OUT_DIR}/metadata.env" <<EOF_METADATA
BASTILLION_VERSION=${VERSION}
BASTILLION_TAG=${TAG}
BASTILLION_JAR_NAME=${JAR_NAME}
BASTILLION_JAR_SHA256=${EXPECTED_SHA256}
BASTILLION_PRERELEASE=${PRERELEASE}
BASTILLION_PUBLISHED_AT=${PUBLISHED_AT}
BASTILLION_RELEASE_URL=${RELEASE_URL}
BASTILLION_JAR_URL=${JAR_URL}
EOF_METADATA

echo
echo "Upstream release prepared successfully:"
echo "  ${OUT_DIR}/bastillion.jar"
echo "  ${OUT_DIR}/LICENSE.md"
echo "  ${OUT_DIR}/3rdPartyLicenses.md"
echo "  ${OUT_DIR}/metadata.env"
echo "  ${OUT_DIR}/release.json"
echo "  ${OUT_DIR}/selected.json"
