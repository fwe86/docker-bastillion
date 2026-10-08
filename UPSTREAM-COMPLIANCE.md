# Bastillion redistribution compliance bundle

Upstream repository: `Loophole-LLC/Bastillion`  
Upstream tag: `v6.0.0`  
Upstream version: `6.0.0`  
Upstream JAR SHA-256: `dc0af1601867bd50e3add126f7ec54bc6cc4671022687c379cbc54151493831c`

This bundle supplements, and does not replace, the upstream Bastillion license.
It preserves legal notices from the official shaded JAR and independently collects
component-specific legal material from the resolved Maven runtime artifacts and npm
packages used by the matching upstream source tag.

For Maven artifacts that omit a complete standard license text from their JARs, the
collector preserves POM/manifest license identity and materializes the corresponding
canonical SPDX license text. Project-specific LICENSE/NOTICE/COPYRIGHT files and source
copyright evidence remain preserved separately and take precedence over that fallback.
If an MIT/BSD Maven module omits its repository-root license from its binary/source JARs,
the collector may recover that project-authored legal file only from the exact GitHub SCM
release tag declared by the component's POM chain; it never substitutes a default branch.

Maven runtime/shaded components collected: **72**  
npm components collected: **7**  
Legal resources surviving inside the upstream shaded JAR: **14**

## Source availability

Where Maven source JARs are published, they are included below each component under
`maven/.../source/`. This intentionally includes more source material than is required
for many permissively licensed components and prevents identified MPL/EPL/GPL/LGPL/CDDL
source-availability obligations from being left to a bare external URL.

For npm components, `COMPONENTS.tsv` records the integrity value and registry tarball
URL from the exact upstream lock file. Full license/notice files from the installed
package are retained under `npm/.../legal/`.

## Upstream shade limitation

Bastillion is redistributed as Loophole's official unmodified shaded JAR. Components
whose Maven metadata survives inside that JAR are independently materialized even if
they are absent from the current dependency:list output. A dependency identified only
as `*-SNAPSHOT` cannot by itself reveal the timestamped snapshot used when the already
published shaded JAR was built; such cases are explicitly reported as warnings.

## Warnings

- org.apache.commons:commons-fileupload2-core:jar:2.0.0-SNAPSHOT is a SNAPSHOT dependency. Its generic Maven version does not identify the timestamped build used when Loophole created the already-shaded release JAR. The official Bastillion release JAR SHA-256 remains the authoritative binary identity.
- org.apache.commons:commons-fileupload2-jakarta:jar:2.0.0-SNAPSHOT is a SNAPSHOT dependency. Its generic Maven version does not identify the timestamped build used when Loophole created the already-shaded release JAR. The official Bastillion release JAR SHA-256 remains the authoritative binary identity.

## Validation

**PASSED** — no missing legal text, unmatched shaded Maven component, or identified source-availability gap was detected by the collector.
