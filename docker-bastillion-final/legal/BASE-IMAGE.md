# Runtime base image licensing

This image is derived from the official `eclipse-temurin:21-jre-noble` image.

The Eclipse Temurin Docker image documentation states that its Dockerfiles and
associated scripts are Apache-2.0 licensed and that the OpenJDK runtime in the
image is licensed under GPL-2.0 with the Classpath Exception. The Ubuntu base
and other installed packages remain under their respective licenses.

The derived image intentionally keeps the legal material already present in the
base image. In particular:

- OpenJDK legal notices remain under `/opt/java/openjdk/legal/`;
- Ubuntu/package copyright material remains under `/usr/share/doc/` where
  supplied by the base image;
- `/opt/bastillion/licenses/base-image/DPKG-PACKAGES.tsv` records the exact
  Debian/Ubuntu package versions present when this image is built;
- `/opt/bastillion/licenses/base-image/JAVA-VERSION.txt` records the runtime
  version;
- `/opt/bastillion/licenses/base-image/UBUNTU-COPYRIGHT-FILES.txt` inventories
  package copyright files present in the image.

OpenJDK/Temurin source and build provenance are published by Eclipse Adoptium,
including the OpenJDK 21 update source mirror and Temurin 21 binary release
metadata:

- https://github.com/adoptium/jdk21u
- https://github.com/adoptium/temurin21-binaries
- https://github.com/adoptium/containers

Ubuntu source packages are published by Ubuntu/Canonical through the Ubuntu
archive infrastructure. The exact installed binary package versions are listed
in `DPKG-PACKAGES.tsv` so the corresponding source package can be identified.

This file is informational. It does not replace any license, copyright, notice,
or source-code obligation applicable to a component in the base image.
