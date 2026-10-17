# Corresponding source for the runtime base image

The published image was built from the immutable base image:

eclipse-temurin:21-jre-noble@sha256:435763596c3be2b929e8bb4282520849804715c3483cfffaa323a7433f2caf71

The exact platform manifests inspected for package/source mapping were:

- linux/amd64: eclipse-temurin:21-jre-noble@sha256:da0f0d242bec39e3fe5c1ac4c415840f03be9cef848c243d723166708e02148c
- linux/arm64: eclipse-temurin:21-jre-noble@sha256:4836d60bd7014ecd293d1acc514afba9dc2c8dc63c3dcd8a0bf3d0ff127d198b

Complete corresponding source material collected for the Ubuntu packages
present in both published architectures and for the Eclipse Temurin/OpenJDK
runtime is available without charge through both of these locations:

- OCI/GHCR artifact: ghcr.io/fwe86/docker-bastillion@sha256:b30cf4aa7c9cd51bb6707b733a99bf595e2910090e8ebc559fc96c5cfcad7ba5
- GitHub Release asset: https://github.com/fwe86/docker-bastillion/releases/download/source-6.0.0-662ffa1d9b79-435763596c3b/docker-bastillion-6.0.0-base-sources-662ffa1d9b79-435763596c3b.tar.gz

Source archive SHA-256:

c99ea4b88159ef14d36bb2cdbd6c98b1c1881bbe10b091c15556fbed6da9247e

To retrieve the immutable OCI artifact by digest:

oras pull ghcr.io/fwe86/docker-bastillion@sha256:b30cf4aa7c9cd51bb6707b733a99bf595e2910090e8ebc559fc96c5cfcad7ba5

The source bundle contains exact binary-to-source package inventories for
linux/amd64 and linux/arm64, the exact Ubuntu source package versions with
their .dsc checksum sets verified, and the exact Temurin/OpenJDK source
archive verified against Adoptium's published SHA-256. Adoptium release
metadata and the exact temurin-build commit archive(s) referenced by that
metadata are included as build-script source and provenance evidence.
