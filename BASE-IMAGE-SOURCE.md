# Corresponding source for the runtime base image

The published image was built from the immutable base image:

eclipse-temurin:21-jre-noble@sha256:0c324fbe2e1455c3159184717440f3b52906ef82a39c4a6efc9edb401d31971a

The exact platform manifests inspected for package/source mapping were:

- linux/amd64: eclipse-temurin:21-jre-noble@sha256:a24fdda21f9ab6482cb01302f09d05bc463f265001f335d2e7d446751a40eb62
- linux/arm64: eclipse-temurin:21-jre-noble@sha256:11ef6037c4f2182d04314669f767ba4ba4670bb81900bb4213f602e752ec1945

Complete corresponding source material collected for the Ubuntu packages
present in both published architectures and for the Eclipse Temurin/OpenJDK
runtime is available without charge through both of these locations:

- OCI/GHCR artifact: ghcr.io/fwe86/docker-bastillion@sha256:3db777415df602e96a5d74e7263a55c965fda562c0413b3a2f58a336e4abef61
- GitHub Release asset: https://github.com/fwe86/docker-bastillion/releases/download/source-5.2.1-1bf44a3647bb-0c324fbe2e14/docker-bastillion-5.2.1-base-sources-1bf44a3647bb-0c324fbe2e14.tar.gz

Source archive SHA-256:

fa25b31328233a0af1396abae5b7fcb137fe25cf6a3e7bb1164c7aa2d1e2fc8e

To retrieve the immutable OCI artifact by digest:

oras pull ghcr.io/fwe86/docker-bastillion@sha256:3db777415df602e96a5d74e7263a55c965fda562c0413b3a2f58a336e4abef61

The source bundle contains exact binary-to-source package inventories for
linux/amd64 and linux/arm64, the exact Ubuntu source package versions with
their .dsc checksum sets verified, and the exact Temurin/OpenJDK source
archive verified against Adoptium's published SHA-256. Adoptium release
metadata and the exact temurin-build commit archive(s) referenced by that
metadata are included as build-script source and provenance evidence.
