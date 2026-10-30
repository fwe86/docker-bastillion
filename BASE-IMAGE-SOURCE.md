# Corresponding source for the runtime base image

The published image was built from the immutable base image:

eclipse-temurin:21-jre-noble@sha256:161310cd5bd41fd549d19cf9f90b614897cb4a1532555c613b43b7e0628fe5d6

The exact platform manifests inspected for package/source mapping were:

- linux/amd64: eclipse-temurin:21-jre-noble@sha256:db724162e4ff5f71fa0a2815026314d9e5e0e9a139f49be1d4717e6930e93341
- linux/arm64: eclipse-temurin:21-jre-noble@sha256:e29bfdff2f7245d8be69ee092651149c026e1b8c2b2d4967c9563963f30076f3

Complete corresponding source material collected for the Ubuntu packages
present in both published architectures and for the Eclipse Temurin/OpenJDK
runtime is available without charge through both of these locations:

- OCI/GHCR artifact: ghcr.io/fwe86/docker-bastillion@sha256:20895df9250c72f46ef4cbe890059493caba7f4897d6a66608be3210ba04a186
- GitHub Release asset: https://github.com/fwe86/docker-bastillion/releases/download/source-6.0.3-65f7b2af6180-161310cd5bd4/docker-bastillion-6.0.3-base-sources-65f7b2af6180-161310cd5bd4.tar.gz

Source archive SHA-256:

47aaf4c01d653b9d1c539e54625c482c1bc9a183628e55637de4ad8a640b21da

To retrieve the immutable OCI artifact by digest:

oras pull ghcr.io/fwe86/docker-bastillion@sha256:20895df9250c72f46ef4cbe890059493caba7f4897d6a66608be3210ba04a186

The source bundle contains exact binary-to-source package inventories for
linux/amd64 and linux/arm64, the exact Ubuntu source package versions with
their .dsc checksum sets verified, and the exact Temurin/OpenJDK source
archive verified against Adoptium's published SHA-256. Adoptium release
metadata and the exact temurin-build commit archive(s) referenced by that
metadata are included as build-script source and provenance evidence.
