# Corresponding source for the runtime base image

The published image was built from the immutable base image:

eclipse-temurin:21-jre-noble@sha256:b4f9d2a0bc273417cf5219b7b832bbf0493ed500b7b57d5001d9f83374659060

The exact platform manifests inspected for package/source mapping were:

- linux/amd64: eclipse-temurin:21-jre-noble@sha256:5163bb00d92964062cec11ae401b1250ba71cad753710f2a4b3bacd90fa61606
- linux/arm64: eclipse-temurin:21-jre-noble@sha256:5e730d47a69254d2350597902ad9e1face33ab3091c124286e86262c525e45de

Complete corresponding source material collected for the Ubuntu packages
present in both published architectures and for the Eclipse Temurin/OpenJDK
runtime is available without charge through both of these locations:

- OCI/GHCR artifact: ghcr.io/fwe86/docker-bastillion@sha256:31725b67b3affa9447b20650eb061c65905b2f3d158baa0a7cc8806f37360d6c
- GitHub Release asset: https://github.com/fwe86/docker-bastillion/releases/download/source-6.0.4-1d39fd976257-b4f9d2a0bc27/docker-bastillion-6.0.4-base-sources-1d39fd976257-b4f9d2a0bc27.tar.gz

Source archive SHA-256:

77dc88b9b7e16545329cb42eb3c9ebc6d4f16717977b4ea631dd175c032e981d

To retrieve the immutable OCI artifact by digest:

oras pull ghcr.io/fwe86/docker-bastillion@sha256:31725b67b3affa9447b20650eb061c65905b2f3d158baa0a7cc8806f37360d6c

The source bundle contains exact binary-to-source package inventories for
linux/amd64 and linux/arm64, the exact Ubuntu source package versions with
their .dsc checksum sets verified, and the exact Temurin/OpenJDK source
archive verified against Adoptium's published SHA-256. Adoptium release
metadata and the exact temurin-build commit archive(s) referenced by that
metadata are included as build-script source and provenance evidence.
