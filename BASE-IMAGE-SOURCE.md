# Corresponding source for the runtime base image

The published image was built from the immutable base image:

eclipse-temurin:21-jre-noble@sha256:977602aad3cf25b74bbb4c8e7532060eef80e1f1288932da35f5fbecd6159b65

The exact platform manifests inspected for package/source mapping were:

- linux/amd64: eclipse-temurin:21-jre-noble@sha256:42b0171b55ff43cbb258de3a1c4a81cb11a96c15b2d8d9a9284a252c1d038605
- linux/arm64: eclipse-temurin:21-jre-noble@sha256:5cb57f10916a5478eaf50306d2676359e4a7bcb1db1c78e3b0fc03ee183a6105

Complete corresponding source material collected for the Ubuntu packages
present in both published architectures and for the Eclipse Temurin/OpenJDK
runtime is available without charge through both of these locations:

- OCI/GHCR artifact: ghcr.io/fwe86/docker-bastillion@sha256:c2f13f930b054fe9b19985f9d67751784362eaf42940a5da18e3407e1b39ee7d
- GitHub Release asset: https://github.com/fwe86/docker-bastillion/releases/download/source-6.0.4-02892eeaacd9-977602aad3cf/docker-bastillion-6.0.4-base-sources-02892eeaacd9-977602aad3cf.tar.gz

Source archive SHA-256:

418d1ecd0f2715e194c625777a00f77b08dd844fdbf83528bd67310b3a275598

To retrieve the immutable OCI artifact by digest:

oras pull ghcr.io/fwe86/docker-bastillion@sha256:c2f13f930b054fe9b19985f9d67751784362eaf42940a5da18e3407e1b39ee7d

The source bundle contains exact binary-to-source package inventories for
linux/amd64 and linux/arm64, the exact Ubuntu source package versions with
their .dsc checksum sets verified, and the exact Temurin/OpenJDK source
archive verified against Adoptium's published SHA-256. Adoptium release
metadata and the exact temurin-build commit archive(s) referenced by that
metadata are included as build-script source and provenance evidence.
