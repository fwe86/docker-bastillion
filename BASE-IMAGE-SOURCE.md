# Corresponding source for the runtime base image

The published image was built from the immutable base image:

eclipse-temurin:21-jre-noble@sha256:cd35bb33859641c5374415826a5951845104093eaa401cbe9d3d9023444f1c13

The exact platform manifests inspected for package/source mapping were:

- linux/amd64: eclipse-temurin:21-jre-noble@sha256:de07a7c89a9430922ee1db1e2f848d75533c7f8f2ab3e4ba5eb52cc4550cdb2a
- linux/arm64: eclipse-temurin:21-jre-noble@sha256:b9322f6071aff3ed7aa0c7fdb3f57d2b56da6ddeaa138fcaa81234f2803141b7

Complete corresponding source material collected for the Ubuntu packages
present in both published architectures and for the Eclipse Temurin/OpenJDK
runtime is available without charge through both of these locations:

- OCI/GHCR artifact: ghcr.io/fwe86/docker-bastillion@sha256:3015bf6e92976253acf8530fecb412b0971cdfb3dce975ddd52ea380e6ce812a
- GitHub Release asset: https://github.com/fwe86/docker-bastillion/releases/download/source-6.0.3-61992e0a9822-cd35bb338596/docker-bastillion-6.0.3-base-sources-61992e0a9822-cd35bb338596.tar.gz

Source archive SHA-256:

1820334d7b1c6b0ab4f49ae63b81f740de7e8dfff35cc4161ae7f7b18bcb7771

To retrieve the immutable OCI artifact by digest:

oras pull ghcr.io/fwe86/docker-bastillion@sha256:3015bf6e92976253acf8530fecb412b0971cdfb3dce975ddd52ea380e6ce812a

The source bundle contains exact binary-to-source package inventories for
linux/amd64 and linux/arm64, the exact Ubuntu source package versions with
their .dsc checksum sets verified, and the exact Temurin/OpenJDK source
archive verified against Adoptium's published SHA-256. Adoptium release
metadata and the exact temurin-build commit archive(s) referenced by that
metadata are included as build-script source and provenance evidence.
