# Corresponding source for the runtime base image

The published image was built from the immutable base image:

eclipse-temurin:21-jre-noble@sha256:22138efd69393501fccd8176ae16b01791ed71ff801b28f0359415389b17c766

The exact platform manifests inspected for package/source mapping were:

- linux/amd64: eclipse-temurin:21-jre-noble@sha256:7fd597bf48c8bb13a7a3fb227f8366dec0423f78775d4b4f7e30409204af8627
- linux/arm64: eclipse-temurin:21-jre-noble@sha256:ad32e01f3e9051e9f69ee3f41bc4826b580569a9f738368bb64b6d2a148824ff

Complete corresponding source material collected for the Ubuntu packages
present in both published architectures and for the Eclipse Temurin/OpenJDK
runtime is available without charge through both of these locations:

- OCI/GHCR artifact: ghcr.io/fwe86/docker-bastillion@sha256:c104c60d3d8e27135b0bac26cc3cb70d10b392a3df5767673956cc99fbfa71fa
- GitHub Release asset: https://github.com/fwe86/docker-bastillion/releases/download/source-5.2.1-b23a9de2c461-22138efd6939/docker-bastillion-5.2.1-base-sources-b23a9de2c461-22138efd6939.tar.gz

Source archive SHA-256:

8918fc7b8a83bd7da776a4c1c2a3a96bc745349fe9c10f1cd2129db29bf85741

To retrieve the immutable OCI artifact by digest:

oras pull ghcr.io/fwe86/docker-bastillion@sha256:c104c60d3d8e27135b0bac26cc3cb70d10b392a3df5767673956cc99fbfa71fa

The source bundle contains exact binary-to-source package inventories for
linux/amd64 and linux/arm64, the exact Ubuntu source package versions with
their .dsc checksum sets verified, and the exact Temurin/OpenJDK source
archive verified against Adoptium's published SHA-256. Adoptium release
metadata and the exact temurin-build commit archive(s) referenced by that
metadata are included as build-script source and provenance evidence.
