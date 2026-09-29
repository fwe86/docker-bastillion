# Licensing notice

The MIT license in `LICENSE` applies only to the original Docker packaging,
GitHub Actions automation, helper scripts, and documentation authored in this
repository.

## Bastillion

The Docker images published by this repository redistribute the official,
unmodified Bastillion release artifact.

Bastillion itself is not MIT-licensed. Bastillion is distributed by Loophole,
LLC under the Prosperity Public License 3.0.0.

The exact upstream license belonging to the Bastillion release most recently
published by this repository is mirrored in `UPSTREAM-LICENSE.md`.

Upstream source code:
https://github.com/Loophole-LLC/Bastillion

Packaging Bastillion into this container does not modify, replace, or bypass
Bastillion's own license terms, commercial licensing requirements, or
application licensing limits.

## Third-party software bundled with Bastillion

Bastillion includes Java/Maven dependencies and frontend npm packages under
their own licenses. The upstream project's own third-party inventory is mirrored
in `UPSTREAM-THIRD-PARTY-LICENSES.md`, but this repository does **not** rely on
that file as the sole compliance record.

For every published image, the build independently resolves and verifies the
runtime Maven/npm component set, preserves component-specific legal material,
materializes available source artifacts where required, recovers exact-tag
project notices where necessary, preserves legal resources surviving inside the
upstream shaded JAR, and SHA-256-verifies the resulting compliance bundle. The
build fails if its legal/source checks cannot be satisfied.

The complete bundle is included in every container under:

`/opt/bastillion/licenses/compliance/`

For compatibility and inspection, legal resources found in the official
Bastillion JAR are also exposed under:

`/opt/bastillion/licenses/jar-notices/`

The official Bastillion JAR itself remains unchanged.

## Runtime base image and corresponding source

The runtime base is the official Eclipse Temurin Java 21 JRE Ubuntu Noble image.
The moving tag `eclipse-temurin:21-jre-noble` is resolved at build time to an
immutable multi-platform manifest digest, and the derived image is built only
from that pinned reference.

Software contained in the base image remains subject to its own license terms.
The derived image retains OpenJDK legal material and Ubuntu package copyright
material. It also includes the Apache-2.0 license applicable to the Temurin
container Dockerfiles/scripts.

Before a derived container image is published, the workflow materializes and
verifies corresponding source for the exact pinned base across both published
architectures. This includes:

- every exact Ubuntu source package/version corresponding to installed binary
  packages, with the `.dsc` source identity and `Checksums-Sha256` files
  verified;
- the exact Temurin/OpenJDK source archive corresponding to `JAVA_VERSION`,
  verified against Adoptium's published SHA-256;
- Adoptium's release metadata/build arguments and archives of the exact
  `temurin-build` commit(s) referenced by that metadata;
- source/evidence for the Temurin container entrypoint script.

The resulting base-source archive is published without charge **before** the
container image both as an immutable OCI artifact in GHCR and as a GitHub
Release asset. The release asset digest is verified, and the source archive
SHA-256 plus immutable retrieval references are embedded in every image under:

`/opt/bastillion/licenses/base-image/CORRESPONDING-SOURCE.md`

The same source pointer and package/source inventories are mirrored into this
repository after a successful build. See `legal/BASE-IMAGE.md` for details.

## SBOM and provenance

Published multi-platform images are built with OCI SBOM and provenance
attestations enabled. These attestations supplement the license and source
bundles; they do not replace license texts, notices, or source-code obligations.
