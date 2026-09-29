FROM eclipse-temurin:21-jre-noble

ARG BASTILLION_VERSION

LABEL org.opencontainers.image.title="Bastillion"
LABEL org.opencontainers.image.description="Unofficial Docker image for Bastillion built from the official upstream release artifact"
LABEL org.opencontainers.image.version="${BASTILLION_VERSION}"
LABEL org.opencontainers.image.source="https://github.com/fwe86/docker-bastillion"
LABEL org.opencontainers.image.url="https://github.com/fwe86/docker-bastillion"
LABEL org.opencontainers.image.documentation="https://github.com/fwe86/docker-bastillion#licensing-and-compliance"

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
    && dpkg-query -W -f='${Package}\t${Version}\n' \
        | sort > /opt/bastillion/licenses/base-image/DPKG-PACKAGES.tsv \
    && java -version 2> /opt/bastillion/licenses/base-image/JAVA-VERSION.txt \
    && find /usr/share/doc -maxdepth 2 -type f -name copyright -print 2>/dev/null \
        | sort > /opt/bastillion/licenses/base-image/UBUNTU-COPYRIGHT-FILES.txt \
    && chown -R 10001:10001 /data/bastillion /opt/bastillion

WORKDIR /opt/bastillion

COPY --chown=10001:10001 .build/bastillion.jar /opt/bastillion/bastillion.jar

COPY --chown=10001:10001 LICENSE /opt/bastillion/licenses/packaging/LICENSE-MIT
COPY --chown=10001:10001 NOTICE.md /opt/bastillion/licenses/packaging/NOTICE.md
COPY --chown=10001:10001 legal/BASE-IMAGE.md /opt/bastillion/licenses/base-image/README.md

COPY --chown=10001:10001 .build/LICENSE.md /opt/bastillion/licenses/upstream/LICENSE.md
COPY --chown=10001:10001 .build/3rdPartyLicenses.md /opt/bastillion/licenses/upstream/3rdPartyLicenses.md

COPY --chown=10001:10001 .build/compliance/ /opt/bastillion/licenses/compliance/
COPY --chown=10001:10001 .build/compliance/upstream-jar/ /opt/bastillion/licenses/jar-notices/

ENV CONFIG_DIR=/data/bastillion/

USER 10001:10001

EXPOSE 8080 8443

ENTRYPOINT ["java", "-DGEN_DB_PASS=true", "-jar", "/opt/bastillion/bastillion.jar"]
