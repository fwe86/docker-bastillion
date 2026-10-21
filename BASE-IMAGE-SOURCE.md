# Corresponding source for the runtime base image

The published image was built from the immutable base image:

eclipse-temurin:21-jre-noble@sha256:35501d3f93173b420ac9001658eb68157e813316b865087e345c187fca422c4c

The exact platform manifests inspected for package/source mapping were:

- linux/amd64: eclipse-temurin:21-jre-noble@sha256:da0f0d242bec39e3fe5c1ac4c415840f03be9cef848c243d723166708e02148c
- linux/arm64: eclipse-temurin:21-jre-noble@sha256:4836d60bd7014ecd293d1acc514afba9dc2c8dc63c3dcd8a0bf3d0ff127d198b

Complete corresponding source material collected for the Ubuntu packages
present in both published architectures and for the Eclipse Temurin/OpenJDK
runtime is available without charge through both of these locations:

- OCI/GHCR artifact: ghcr.io/fwe86/docker-bastillion@sha256:baf0725d0eeba09765d9eef65cf76a614b4d038893dc0b09f852135e14af1f72
- GitHub Release asset: https://github.com/fwe86/docker-bastillion/releases/download/source-6.0.1-e565920ab1fb-35501d3f9317/docker-bastillion-6.0.1-base-sources-e565920ab1fb-35501d3f9317.tar.gz

Source archive SHA-256:

abe2ae085ee47386843b4aed41090c5f8612e20f5840c29b9010fdd8638b7507

To retrieve the immutable OCI artifact by digest:

oras pull ghcr.io/fwe86/docker-bastillion@sha256:baf0725d0eeba09765d9eef65cf76a614b4d038893dc0b09f852135e14af1f72

The source bundle contains exact binary-to-source package inventories for
linux/amd64 and linux/arm64, the exact Ubuntu source package versions with
their .dsc checksum sets verified, and the exact Temurin/OpenJDK source
archive verified against Adoptium's published SHA-256. Adoptium release
metadata and the exact temurin-build commit archive(s) referenced by that
metadata are included as build-script source and provenance evidence.
