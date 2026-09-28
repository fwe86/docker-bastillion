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

Before publishing:

1. the official Bastillion JAR is downloaded;
2. its SHA-256 digest is verified against GitHub release metadata;
3. the exact upstream license files are downloaded from the matching release tag;
4. license and notice resources present in the official JAR are preserved separately in the image;
5. the container is built and started;
6. the running application is tested;
7. the multi-platform image is published to GHCR;
8. `.upstream` and the mirrored upstream license files are updated.

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

## Licensing

The MIT license in `LICENSE` applies only to the original Docker packaging,
GitHub Actions automation, and documentation authored in this repository.

Bastillion itself is not MIT-licensed. The Docker images redistribute the
official Bastillion release artifact unchanged. Bastillion is distributed
under the Prosperity Public License 3.0.0 by Loophole, LLC.

The exact license files belonging to the Bastillion version most recently
published by this repository are mirrored as:

- `UPSTREAM-LICENSE.md`
- `UPSTREAM-THIRD-PARTY-LICENSES.md`

The same upstream files are included in each image under:

`/opt/bastillion/licenses/upstream/`

License and notice resources present inside the official Bastillion JAR are
also exposed under:

`/opt/bastillion/licenses/jar-notices/`

See `NOTICE.md` for the licensing boundary between this repository's original
work, Bastillion, the Java runtime image, and other third-party software.

This project is not affiliated with or endorsed by the Bastillion project or
Loophole, LLC.
