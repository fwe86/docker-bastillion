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
https://github.com/bastillion-io/Bastillion

Packaging Bastillion into this container does not modify, replace, or bypass
Bastillion's own license terms, commercial licensing requirements, or
application licensing limits.

## Third-party software bundled with Bastillion

Bastillion includes Java/Maven dependencies and frontend npm packages under
their own licenses. The upstream project's own third-party inventory is mirrored
in `UPSTREAM-THIRD-PARTY-LICENSES.md`, but this repository does **not** rely on
that file as the sole compliance record.

For every published image, the build independently:

1. resolves the runtime Maven dependency set from the exact upstream release
   tag;
2. materializes published Maven source JARs where available;
3. installs the exact npm package versions from the upstream lock file without
   running package scripts;
4. preserves component-specific LICENSE, LICENCE, NOTICE, COPYING, COPYRIGHT,
   DEPENDENCIES, and ABOUT resources from the original dependency artifacts;
5. preserves the legal resources that survived inside Loophole's official
   shaded Bastillion JAR;
6. records the dependency versions, declared licenses, artifact hashes, source
   locations, and source-materialization status;
7. fails the build if a Maven/npm component has no full legal text/notice
   material, or if a source-requiring Maven component is detected but no source
   artifact can be materialized;
8. verifies SHA-256 hashes for the complete generated compliance bundle before
   publication.

The complete bundle is included in every container under:

`/opt/bastillion/licenses/compliance/`

For compatibility and easy inspection, the legal resources found in the
official Bastillion JAR are also exposed under:

`/opt/bastillion/licenses/jar-notices/`

The generated summary and component inventory for the most recently published
version are mirrored back to the repository as `UPSTREAM-COMPLIANCE.md` and
`UPSTREAM-COMPONENTS.tsv` after a successful build.

The official Bastillion JAR itself remains unchanged.

## Runtime base image

The image is based on the official Eclipse Temurin Java 21 JRE image using the
Ubuntu Noble variant. Software contained in that base image remains subject to
its own license terms.

The derived image retains the base image's OpenJDK legal directory and Ubuntu
package documentation. It also records the installed package versions and Java
runtime version under:

`/opt/bastillion/licenses/base-image/`

Additional base-image licensing and source-location information is provided in
`legal/BASE-IMAGE.md` and is copied into the image.

## SBOM and provenance

Published multi-platform images are built with OCI SBOM and provenance
attestations enabled. These attestations supplement the license bundle; they do
not replace license texts, notices, or source-code obligations.
