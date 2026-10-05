# Corresponding source for the runtime base image

The published image was built from the immutable base image:

eclipse-temurin:21-jre-noble@sha256:000fd431958bc81a24abe1e8e5f0f0fd3ae365a594bd50aadb20696805f9408c

The exact platform manifests inspected for package/source mapping were:

- linux/amd64: eclipse-temurin:21-jre-noble@sha256:7fd597bf48c8bb13a7a3fb227f8366dec0423f78775d4b4f7e30409204af8627
- linux/arm64: eclipse-temurin:21-jre-noble@sha256:ad32e01f3e9051e9f69ee3f41bc4826b580569a9f738368bb64b6d2a148824ff

Complete corresponding source material collected for the Ubuntu packages
present in both published architectures and for the Eclipse Temurin/OpenJDK
runtime is available without charge through both of these locations:

- OCI/GHCR artifact: ghcr.io/fwe86/docker-bastillion@sha256:d8d06b7ff3186998f51eaaa666393ce464f42f3bdd63675b68f627fc02b17c15
- GitHub Release asset: https://github.com/fwe86/docker-bastillion/releases/download/source-5.2.1-63fc7bc0907d-000fd431958b/docker-bastillion-5.2.1-base-sources-63fc7bc0907d-000fd431958b.tar.gz

Source archive SHA-256:

ed593e5ec004df30ef57b48c5ba63dc0c706139bdea8227faa6c6bc454ec6d93

To retrieve the immutable OCI artifact by digest:

oras pull ghcr.io/fwe86/docker-bastillion@sha256:d8d06b7ff3186998f51eaaa666393ce464f42f3bdd63675b68f627fc02b17c15

The source bundle contains exact binary-to-source package inventories for
linux/amd64 and linux/arm64, the exact Ubuntu source package versions with
their .dsc checksum sets verified, and the exact Temurin/OpenJDK source
archive verified against Adoptium's published SHA-256. Adoptium release
metadata and the exact temurin-build commit archive(s) referenced by that
metadata are included as build-script source and provenance evidence.
