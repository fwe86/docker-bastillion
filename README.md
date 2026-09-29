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

The repository checks once per day for the latest stable Bastillion release.

A new image is built when:

- a new stable Bastillion release is available;
- the upstream release artifact changes;
- this repository is changed on the `main` branch;
- the workflow is started manually.

Pre-releases are ignored.

Before publishing, the workflow:

1. downloads the official Bastillion JAR;
2. verifies its SHA-256 digest against GitHub release metadata;
3. downloads the exact upstream license, third-party inventory, Maven POM, and
   npm lock metadata from the matching release tag;
4. independently resolves the runtime Maven dependency set and also materializes
   Maven components whose coordinates survive only inside the shaded Bastillion JAR;
5. obtains available Maven source JARs, preserves component-specific legal
   resources from binary/source artifacts, resolves inherited POM license metadata,
   and adds canonical SPDX license texts when upstream JARs omit the full standard
   license text;
6. installs the exact npm dependency set from `package-lock.json` without
   executing package scripts and preserves each package's legal files;
7. preserves legal resources still present in the official shaded Bastillion
   JAR;
8. generates and SHA-256-verifies an independent compliance bundle;
9. builds and starts a verification image and checks that the legal material is
   present inside it;
10. starts Bastillion and verifies that the application responds;
11. publishes the multi-platform image with OCI SBOM and provenance
    attestations;
12. updates `.upstream` and the repository's upstream license/compliance
    snapshots.

The build is fail-closed for the compliance checks performed by the collector:
a missing component legal text/notice or an identified source-availability gap
prevents publication.

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

The complete generated compliance bundle is embedded in each image under:

`/opt/bastillion/licenses/compliance/`

It contains component-specific Maven and npm legal files, Maven source JARs
where published, inherited POM/manifest license metadata, canonical SPDX full
license texts used only as a fallback when project artifacts omit them, and —
for Maven modules that omit a repository-root MIT/BSD notice from their JARs —
project-authored legal files recovered from the exact GitHub SCM release tag
declared by the module's POM chain. It also contains hashes, the dependency
inventory, and the legal resources preserved from the official Bastillion JAR. Maven coordinates found only inside the shaded release JAR are
materialized and checked as well.

Base-image licensing information is retained separately under:

`/opt/bastillion/licenses/base-image/`

OpenJDK's original legal material remains available at:

`/opt/java/openjdk/legal/`

See `NOTICE.md` for the licensing boundary between this repository's original
work, Bastillion, its bundled dependencies, and the runtime base image.

This project is not affiliated with or endorsed by the Bastillion project or
Loophole, LLC.
