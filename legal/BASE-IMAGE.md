# Runtime base image licensing and corresponding source

Published images are derived from the official `eclipse-temurin:21-jre-noble`
image. The build resolves that moving tag to an immutable multi-platform image
index digest before any image is built and then uses only the digest-pinned index
reference for BuildKit. For per-architecture inspection, the workflow separately
resolves and uses the immutable child-manifest digest for `linux/amd64` and
`linux/arm64`; this avoids relying on mutable tag resolution and avoids treating a
multi-platform index digest as though it were a single-platform manifest. The
index digest and both child-manifest digests are recorded in `.upstream` and in
the generated source/compliance evidence.

Eclipse Temurin documents that the OpenJDK runtime is licensed under GPL-2.0
with the Classpath Exception, while the Temurin container Dockerfiles and
associated scripts are Apache-2.0 licensed. Ubuntu packages in the base image
remain subject to their respective licenses.

## Exact corresponding-source publication

Before a docker-bastillion image is published, the workflow independently
materializes corresponding source for the exact pinned runtime base for both
published architectures (`linux/amd64` and `linux/arm64`). Publication is
fail-closed: the container image is not published unless this source bundle has
been created, verified, and made available.

For every installed Ubuntu/Debian binary package, the workflow records the
binary package/version and the package's `source:Package` and `source:Version`
metadata. It then downloads that exact Ubuntu source package from Launchpad.
The `.dsc` identity is checked and every file listed in its
`Checksums-Sha256` section is verified before publication.

For the Temurin/OpenJDK runtime, the workflow reads the exact `JAVA_VERSION`
from both platform variants, requires the versions to match, downloads the
corresponding official Adoptium OpenJDK source archive, and verifies it against
Adoptium's published SHA-256. Adoptium's checksum, signature, and release metadata are kept with the
archive. The release metadata identifies the exact `temurin-build` commit and
build arguments used for the release; the workflow also archives every exact
`temurin-build` commit referenced by the source/JRE metadata. This preserves the
build-script source used to control compilation and packaging. The base image's
`__cacert_entrypoint.sh` source is also preserved as evidence of the
Apache-2.0-licensed container script, and the full Apache-2.0 license is included
in the derived image.

The verified base-source bundle is published **before** the derived image in two
independent locations:

1. as an OCI artifact in the same GHCR package, addressable by immutable digest;
2. as a GitHub Release asset with its SHA-256 verified against GitHub's release
   asset metadata.

Every published image embeds `/opt/bastillion/licenses/base-image/CORRESPONDING-SOURCE.md`
and `/opt/bastillion/licenses/base-image/SOURCE-LOCATION.env`, which identify
the immutable base-image digest, the immutable OCI source-artifact digest, the
GitHub Release source URL, and the source archive SHA-256. The same pointer is
mirrored to `BASE-IMAGE-SOURCE.md` after a successful build.

This supplies actual corresponding source rather than relying on a written
offer or only on mutable upstream links.

## Legal material retained in the image

The derived image also intentionally preserves the legal material already
present in the pinned base image. In particular:

- OpenJDK legal notices remain under `/opt/java/openjdk/legal/`;
- Ubuntu/package copyright material remains under `/usr/share/doc/` where
  supplied by the base image;
- `/opt/bastillion/licenses/base-image/DPKG-PACKAGES.tsv` records installed
  binary versions and their source package/version mapping;
- `/opt/bastillion/licenses/base-image/JAVA-VERSION.txt` records the runtime
  version;
- `/opt/bastillion/licenses/base-image/UBUNTU-COPYRIGHT-FILES.txt` inventories
  package copyright files present in the image;
- `/opt/bastillion/licenses/base-image/ADOPTIUM-CONTAINERS-LICENSE-APACHE-2.0.txt`
  contains the Apache-2.0 license for the Temurin container scripts.

The generated source archive contains additional per-architecture inventories,
`inventory/PLATFORM-MANIFESTS.tsv` tying each architecture to its exact immutable
child-manifest digest, hashes of legal files retained by the base image, the exact
Ubuntu source packages, and the verified Temurin/OpenJDK source archive.

Each component remains governed by its own upstream license. Nothing in this
repository relicenses base-image software.
