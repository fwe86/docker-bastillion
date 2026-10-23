# Corresponding source for the runtime base image

The published image was built from the immutable base image:

eclipse-temurin:21-jre-noble@sha256:35501d3f93173b420ac9001658eb68157e813316b865087e345c187fca422c4c

The exact platform manifests inspected for package/source mapping were:

- linux/amd64: eclipse-temurin:21-jre-noble@sha256:da0f0d242bec39e3fe5c1ac4c415840f03be9cef848c243d723166708e02148c
- linux/arm64: eclipse-temurin:21-jre-noble@sha256:4836d60bd7014ecd293d1acc514afba9dc2c8dc63c3dcd8a0bf3d0ff127d198b

Complete corresponding source material collected for the Ubuntu packages
present in both published architectures and for the Eclipse Temurin/OpenJDK
runtime is available without charge through both of these locations:

- OCI/GHCR artifact: ghcr.io/fwe86/docker-bastillion@sha256:fe8212befed78f2ad90fbb44ac23075b6410a7b70aa8f2b5997873debd06fcdd
- GitHub Release asset: https://github.com/fwe86/docker-bastillion/releases/download/source-6.0.3-52c050a6a791-35501d3f9317/docker-bastillion-6.0.3-base-sources-52c050a6a791-35501d3f9317.tar.gz

Source archive SHA-256:

abe2ae085ee47386843b4aed41090c5f8612e20f5840c29b9010fdd8638b7507

To retrieve the immutable OCI artifact by digest:

oras pull ghcr.io/fwe86/docker-bastillion@sha256:fe8212befed78f2ad90fbb44ac23075b6410a7b70aa8f2b5997873debd06fcdd

The source bundle contains exact binary-to-source package inventories for
linux/amd64 and linux/arm64, the exact Ubuntu source package versions with
their .dsc checksum sets verified, and the exact Temurin/OpenJDK source
archive verified against Adoptium's published SHA-256. Adoptium release
metadata and the exact temurin-build commit archive(s) referenced by that
metadata are included as build-script source and provenance evidence.
