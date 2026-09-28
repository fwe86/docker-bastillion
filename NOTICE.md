# Licensing notice

The MIT license in `LICENSE` applies only to the original Docker packaging,
GitHub Actions automation, and documentation authored in this repository.

## Bastillion

The Docker images published by this repository redistribute the official,
unmodified Bastillion release artifact.

Bastillion itself is not MIT-licensed. Bastillion is distributed by
Loophole, LLC under the Prosperity Public License 3.0.0.

The exact upstream license belonging to the Bastillion release most recently
published by this repository is mirrored in `UPSTREAM-LICENSE.md`.

Upstream source code:
https://github.com/bastillion-io/Bastillion

Packaging Bastillion into this container does not modify, replace, or bypass
Bastillion's own license terms, commercial licensing requirements, or
application licensing limits.

## Third-party software

Bastillion includes third-party dependencies under their own licenses. The
third-party license inventory supplied with the exact upstream release is
mirrored in `UPSTREAM-THIRD-PARTY-LICENSES.md`.

Every build also preserves all LICENSE, NOTICE, COPYING, and COPYRIGHT
resources found inside the official Bastillion JAR and exposes them in the
container under:

`/opt/bastillion/licenses/jar-notices/`

The official Bastillion JAR itself is redistributed unchanged.

## Runtime base image

The image is based on the official Eclipse Temurin Java runtime image.
Software contained in that image remains subject to its respective license
terms and notices.
