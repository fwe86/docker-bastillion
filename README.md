# docker-bastillion

Unofficial Docker image for [Bastillion](https://github.com/Loophole-LLC/Bastillion), built automatically from the official upstream release artifact without modifying Bastillion itself.

## Image

`ghcr.io/fwe86/docker-bastillion`

## Tags

- `latest`
- exact Bastillion version, for example `5.2.1`

## Supported platforms

- `linux/amd64`
- `linux/arm64`

## Automatic builds

GitHub Actions checks once per day for the latest stable Bastillion release.

A new image is built when:

- a new stable Bastillion release is available;
- the release artifact digest changes;
- this repository changes on `main`;
- the workflow is started manually.

Pre-releases are ignored.

Before publishing, the official Bastillion JAR is verified against the SHA-256 digest supplied by the GitHub release metadata. The image is then built and a real Bastillion container is started and checked before the multi-platform image is published to GHCR.

The last successfully published upstream state is stored in `.upstream`.

## Persistence

Persistent Bastillion data is stored in:

`/data/bastillion`

The container runs as UID/GID `10001:10001`.

## Ports

- HTTPS: `8443`
- HTTP behind a reverse proxy: `8080`

For operation behind a TLS-terminating reverse proxy:

- `TLS_ENABLED=false`
- `PORT=8080`

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

The Docker packaging and automation in this repository are licensed under the MIT License.

Bastillion itself remains under its upstream license. The matching `LICENSE.md` and `3rdPartyLicenses.md` from the exact Bastillion release are included in every generated image.

This repository does not modify Bastillion and is not affiliated with or endorsed by the Bastillion project or Loophole, LLC.
