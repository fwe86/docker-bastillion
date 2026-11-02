# Corresponding source for the runtime base image

The published image was built from the immutable base image:

eclipse-temurin:21-jre-noble@sha256:0eda5830ed7b669abc246a8dc520ea8a23cab06f9a8d4b6964109e2f2394e46f

The exact platform manifests inspected for package/source mapping were:

- linux/amd64: eclipse-temurin:21-jre-noble@sha256:db724162e4ff5f71fa0a2815026314d9e5e0e9a139f49be1d4717e6930e93341
- linux/arm64: eclipse-temurin:21-jre-noble@sha256:e29bfdff2f7245d8be69ee092651149c026e1b8c2b2d4967c9563963f30076f3

Complete corresponding source material collected for the Ubuntu packages
present in both published architectures and for the Eclipse Temurin/OpenJDK
runtime is available without charge through both of these locations:

- OCI/GHCR artifact: ghcr.io/fwe86/docker-bastillion@sha256:3a56738a49fbb827ca9def0070a3fc78ff881a5a33539fa8675ac225d7590c99
- GitHub Release asset: https://github.com/fwe86/docker-bastillion/releases/download/source-6.0.3-d7253603a3b1-0eda5830ed7b/docker-bastillion-6.0.3-base-sources-d7253603a3b1-0eda5830ed7b.tar.gz

Source archive SHA-256:

00bbbf7cbe20ba7d9c514e8629a04417abcb313068e321e90c3f2c30f808dcc1

To retrieve the immutable OCI artifact by digest:

oras pull ghcr.io/fwe86/docker-bastillion@sha256:3a56738a49fbb827ca9def0070a3fc78ff881a5a33539fa8675ac225d7590c99

The source bundle contains exact binary-to-source package inventories for
linux/amd64 and linux/arm64, the exact Ubuntu source package versions with
their .dsc checksum sets verified, and the exact Temurin/OpenJDK source
archive verified against Adoptium's published SHA-256. Adoptium release
metadata and the exact temurin-build commit archive(s) referenced by that
metadata are included as build-script source and provenance evidence.
