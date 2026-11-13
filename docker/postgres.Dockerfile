# Preserve the verified PostgreSQL engine and replace the old Go-based privilege
# switcher with Alpine's small C implementation. The entrypoint drops to postgres.
FROM postgres@sha256:1018733457011bf88d81db98cf43aac6d5150afc18787dbe204771fedf80ff95
RUN apk add --no-cache su-exec=0.3-r0 && rm /usr/local/bin/gosu
RUN ln -s /sbin/su-exec /usr/local/bin/gosu
HEALTHCHECK --interval=10s --timeout=5s CMD pg_isready -U uag_owner -d uag
