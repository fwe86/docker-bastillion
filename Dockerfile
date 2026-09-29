ARG BASE_IMAGE_REF
FROM ${BASE_IMAGE_REF}

ARG BASTILLION_VERSION
ARG BASE_IMAGE_NAME
ARG BASE_IMAGE_DIGEST
ARG BASE_SOURCE_OCI_REF
ARG BASE_SOURCE_OCI_DIGEST
ARG BASE_SOURCE_RELEASE_URL
ARG BASE_SOURCE_SHA256

LABEL org.opencontainers.image.title="Bastillion"
LABEL org.opencontainers.image.description="Unofficial Docker image for Bastillion built from the official upstream release artifact"
LABEL org.opencontainers.image.version="${BASTILLION_VERSION}"
LABEL org.opencontainers.image.source="https://github.com/fwe86/docker-bastillion"
LABEL org.opencontainers.image.url="https://github.com/fwe86/docker-bastillion"
LABEL org.opencontainers.image.documentation="https://github.com/fwe86/docker-bastillion#licensing-and-compliance"
LABEL org.opencontainers.image.base.name="${BASE_IMAGE_NAME}"
LABEL org.opencontainers.image.base.digest="${BASE_IMAGE_DIGEST}"
LABEL io.github.fwe86.docker-bastillion.base-source.oci-ref="${BASE_SOURCE_OCI_REF}"
LABEL io.github.fwe86.docker-bastillion.base-source.oci-digest="${BASE_SOURCE_OCI_DIGEST}"
LABEL io.github.fwe86.docker-bastillion.base-source.release-url="${BASE_SOURCE_RELEASE_URL}"
LABEL io.github.fwe86.docker-bastillion.base-source.sha256="${BASE_SOURCE_SHA256}"

RUN groupadd --gid 10001 bastillion \
    && useradd \
        --uid 10001 \
        --gid 10001 \
        --home-dir /opt/bastillion \
        --create-home \
        --shell /usr/sbin/nologin \
        bastillion \
    && mkdir -p \
        /data/bastillion \
        /opt/bastillion/licenses/packaging \
        /opt/bastillion/licenses/upstream \
        /opt/bastillion/licenses/compliance \
        /opt/bastillion/licenses/jar-notices \
        /opt/bastillion/licenses/base-image \
    && dpkg-query -W -f='${binary:Package}\t${Version}\t${source:Package}\t${source:Version}\n' \
        | sort > /opt/bastillion/licenses/base-image/DPKG-PACKAGES.tsv \
    && java -version 2> /opt/bastillion/licenses/base-image/JAVA-VERSION.txt \
    && find /usr/share/doc -maxdepth 2 \( -type f -o -type l \) -name copyright -print 2>/dev/null \
        | sort > /opt/bastillion/licenses/base-image/UBUNTU-COPYRIGHT-FILES.txt \
    && printf '%s\n' \
        "BASE_IMAGE_NAME=${BASE_IMAGE_NAME}" \
        "BASE_IMAGE_DIGEST=${BASE_IMAGE_DIGEST}" \
        "BASE_SOURCE_OCI_REF=${BASE_SOURCE_OCI_REF}" \
        "BASE_SOURCE_OCI_DIGEST=${BASE_SOURCE_OCI_DIGEST}" \
        "BASE_SOURCE_RELEASE_URL=${BASE_SOURCE_RELEASE_URL}" \
        "BASE_SOURCE_SHA256=${BASE_SOURCE_SHA256}" \
        > /opt/bastillion/licenses/base-image/SOURCE-LOCATION.env \
    && chown -R 10001:10001 /data/bastillion /opt/bastillion

WORKDIR /opt/bastillion

COPY --chown=10001:10001 .build/bastillion.jar /opt/bastillion/bastillion.jar

COPY --chown=10001:10001 LICENSE /opt/bastillion/licenses/packaging/LICENSE-MIT
COPY --chown=10001:10001 NOTICE.md /opt/bastillion/licenses/packaging/NOTICE.md
COPY --chown=10001:10001 legal/BASE-IMAGE.md /opt/bastillion/licenses/base-image/README.md
COPY --chown=10001:10001 legal/ADOPTIUM-CONTAINERS-LICENSE-APACHE-2.0.txt /opt/bastillion/licenses/base-image/ADOPTIUM-CONTAINERS-LICENSE-APACHE-2.0.txt
COPY --chown=10001:10001 .build/base-source-pointer.md /opt/bastillion/licenses/base-image/CORRESPONDING-SOURCE.md

COPY --chown=10001:10001 .build/LICENSE.md /opt/bastillion/licenses/upstream/LICENSE.md
COPY --chown=10001:10001 .build/3rdPartyLicenses.md /opt/bastillion/licenses/upstream/3rdPartyLicenses.md

COPY --chown=10001:10001 .build/compliance/ /opt/bastillion/licenses/compliance/
COPY --chown=10001:10001 .build/compliance/upstream-jar/ /opt/bastillion/licenses/jar-notices/

ENV CONFIG_DIR=/data/bastillion/

USER 10001:10001

EXPOSE 8080 8443

ENTRYPOINT ["java", "-DGEN_DB_PASS=true", "-jar", "/opt/bastillion/bastillion.jar"]
