# docker-bastillion

Unofficial Docker image for [Bastillion](https://github.com/Loophole-LLC/Bastillion).

Container image:

`ghcr.io/fwe86/docker-bastillion`

## Tags

- `latest`
- exact Bastillion version, for example `5.2.1`

## Supported platforms

- `linux/amd64`
- `linux/arm64`

## Automatic builds

The repository checks once per day for the latest stable Bastillion release and
for changes to the runtime base-image digest.

A new image is built when:

- a new stable Bastillion release is available;
- the upstream release artifact changes;
- `eclipse-temurin:21-jre-noble` resolves to a different multi-platform digest;
- this repository is changed on the `main` branch;
- the workflow is started manually.

Pre-releases are ignored.

Before publishing, the workflow:

1. resolves the Temurin base tag to an immutable manifest digest and requires
   exactly one `linux/amd64` and one `linux/arm64` platform image;
2. downloads the official Bastillion JAR and verifies its SHA-256 against the
   GitHub release metadata;
3. downloads the exact upstream license, third-party inventory, Maven POM, and
   npm lock metadata from the matching Bastillion release tag;
4. independently resolves the runtime Maven dependency set and also materializes
   Maven components whose coordinates survive only inside the shaded Bastillion JAR;
5. obtains available Maven source JARs, preserves component-specific legal
   resources from binary/source artifacts, resolves inherited POM license metadata,
   and adds canonical SPDX license texts when upstream JARs omit the full standard
   license text;
6. installs the exact npm dependency set from `package-lock.json` without
   executing package scripts and preserves each package's legal files;
7. preserves legal resources still present in the official shaded Bastillion
   JAR and verifies the generated third-party compliance bundle;
8. inventories both architecture variants of the pinned Temurin/Ubuntu base,
   maps every installed binary package to its exact Ubuntu source package and
   version, downloads those source packages, and verifies the `.dsc`
   `Checksums-Sha256` entries;
9. downloads the exact Temurin/OpenJDK source archive corresponding to the
   runtime `JAVA_VERSION`, verifies Adoptium's published SHA-256, preserves the
   release metadata/build arguments, and archives the exact `temurin-build`
   commit(s) referenced by that metadata;
10. creates a deterministic corresponding-source archive for the base image and
    publishes it, before the container image, both as an immutable OCI/GHCR
    artifact and as a GitHub Release asset;
11. builds and starts a verification image, checks the embedded license/source
    pointers and hashes, and verifies that Bastillion responds;
12. publishes the multi-platform image with OCI SBOM and provenance
    attestations;
13. updates `.upstream` and the repository's compliance/source snapshots.

The build is fail-closed for the compliance checks performed by the collectors.
A missing legal text, an identified source-availability gap, a missing exact
Ubuntu source package, a Temurin source checksum mismatch, or failure to publish
and verify the base corresponding-source archive prevents image publication.

## Persistence

Persistent Bastillion data is stored in:

`/data/bastillion`

## Ports

Default HTTPS:

`8443`

HTTP behind a reverse proxy:

`8080`

Set:

- `TLS_ENABLED=false`
- `PORT=8080`

when TLS is terminated by a reverse proxy.

## Example

```yaml
services:
  bastillion:
    image: ghcr.io/fwe86/docker-bastillion:latest
    container_name: bastillion
    environment:
      TLS_ENABLED: "false"
      PORT: "8080"
    volumes:
      - ./data:/data/bastillion
    restart: unless-stopped
```

## Licensing and compliance

The MIT license in `LICENSE` applies only to the original Docker packaging,
GitHub Actions automation, helper scripts, and documentation authored in this
repository.

Bastillion itself is not MIT-licensed. The Docker images redistribute the
official Bastillion release artifact unchanged. Bastillion is distributed
under the Prosperity Public License 3.0.0 by Loophole, LLC.

The exact upstream files belonging to the Bastillion version most recently
published by this repository are mirrored as:

- `UPSTREAM-LICENSE.md`
- `UPSTREAM-THIRD-PARTY-LICENSES.md`

After a successful compliant build, the independently generated current-version
summary and component inventory are mirrored as:

- `UPSTREAM-COMPLIANCE.md`
- `UPSTREAM-COMPONENTS.tsv`

The complete generated Bastillion/dependency compliance bundle is embedded in
each image under:

`/opt/bastillion/licenses/compliance/`

It contains component-specific Maven and npm legal files, Maven source JARs
where published, inherited POM/manifest license metadata, canonical SPDX full
license texts used only as a fallback when project artifacts omit them, and —
for Maven modules that omit a repository-root MIT/BSD notice from their JARs —
project-authored legal files recovered from the exact GitHub SCM release tag
declared by the module's POM chain. Maven coordinates found only inside the
shaded release JAR are materialized and checked as well.

### Runtime base corresponding source

Published builds no longer rely on the mutable Temurin tag as the build input.
The workflow resolves `eclipse-temurin:21-jre-noble` to an immutable digest and
uses that pinned reference for both architectures.

Before the image is published, exact corresponding source for the pinned base
is collected and made available through both GHCR and a GitHub Release. The
immutable retrieval information is embedded in every image at:

`/opt/bastillion/licenses/base-image/CORRESPONDING-SOURCE.md`

and is mirrored after a successful build as:

`BASE-IMAGE-SOURCE.md`

The repository also mirrors the exact binary-to-source package inventories and
the union of source package/version tuples as:

- `BASE-IMAGE-PACKAGES-amd64.tsv`
- `BASE-IMAGE-PACKAGES-arm64.tsv`
- `BASE-IMAGE-SOURCE-PACKAGES.tsv`

The source archive itself contains the exact Ubuntu source packages for the
installed base packages, verified against their `.dsc` SHA-256 lists, plus the
exact Temurin/OpenJDK source archive verified against Adoptium's published
SHA-256, the Adoptium release metadata/build arguments, and exact archives of
the `temurin-build` commit(s) referenced by that metadata. It is published
before the derived image; failure to publish or verify
it blocks the container release.

Base-image legal material is retained separately under:

`/opt/bastillion/licenses/base-image/`

OpenJDK's original legal material remains available at:

`/opt/java/openjdk/legal/`

See `NOTICE.md` and `legal/BASE-IMAGE.md` for the licensing boundary and source
publication details.

This project is not affiliated with or endorsed by the Bastillion project or
Loophole, LLC.
