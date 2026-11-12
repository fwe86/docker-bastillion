# Corresponding source for the runtime base image

The published image was built from the immutable base image:

eclipse-temurin:21-jre-noble@sha256:0d57a8e90c2bb844c5a8e1b2b71e11eff06dad7edcfd803cd21ed4ae203b2515

The exact platform manifests inspected for package/source mapping were:

- linux/amd64: eclipse-temurin:21-jre-noble@sha256:42b0171b55ff43cbb258de3a1c4a81cb11a96c15b2d8d9a9284a252c1d038605
- linux/arm64: eclipse-temurin:21-jre-noble@sha256:5cb57f10916a5478eaf50306d2676359e4a7bcb1db1c78e3b0fc03ee183a6105

Complete corresponding source material collected for the Ubuntu packages
present in both published architectures and for the Eclipse Temurin/OpenJDK
runtime is available without charge through both of these locations:

- OCI/GHCR artifact: ghcr.io/fwe86/docker-bastillion@sha256:815348800d95302a64ef7bc811585e253181a45dd23a9c0ec75a3dc2106977f3
- GitHub Release asset: https://github.com/fwe86/docker-bastillion/releases/download/source-6.0.4-6535b4aba7f0-0d57a8e90c2b/docker-bastillion-6.0.4-base-sources-6535b4aba7f0-0d57a8e90c2b.tar.gz

Source archive SHA-256:

9ac8b52536b8233c221e8c67372cffeb1150833fdd2df31012934980509cbfab

To retrieve the immutable OCI artifact by digest:

oras pull ghcr.io/fwe86/docker-bastillion@sha256:815348800d95302a64ef7bc811585e253181a45dd23a9c0ec75a3dc2106977f3

The source bundle contains exact binary-to-source package inventories for
linux/amd64 and linux/arm64, the exact Ubuntu source package versions with
their .dsc checksum sets verified, and the exact Temurin/OpenJDK source
archive verified against Adoptium's published SHA-256. Adoptium release
metadata and the exact temurin-build commit archive(s) referenced by that
metadata are included as build-script source and provenance evidence.
