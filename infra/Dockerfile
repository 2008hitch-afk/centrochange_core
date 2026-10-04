FROM frappe/erpnext:v16.32.0@sha256:481168fa7ba34bb9803e80139dff6df80bc161352cc7b478ae90b0c0da814f90

# Builder is fetched by its official release tag, then its immutable commit is asserted.
ARG BUILDER_TAG=v1.33.0
ARG BUILDER_REF=41987c064da4650e6901b5da82b7c76add452ebf
ARG HEALTHCARE_TAG=v16.5.2
ARG HEALTHCARE_REF=934d6c162868139dfbe80c23d6102adb7ec25adb

USER frappe
WORKDIR /home/frappe/frappe-bench

RUN git config --global http.version HTTP/1.1 \
    && bench get-app --branch "${BUILDER_TAG}" builder https://github.com/frappe/builder.git \
    && test "$(git -C apps/builder rev-parse HEAD)" = "${BUILDER_REF}"

RUN bench get-app --branch "${HEALTHCARE_TAG}" healthcare https://github.com/earthians/marley.git \
    && test "$(git -C apps/healthcare rev-parse HEAD)" = "${HEALTHCARE_REF}"

COPY --chown=frappe:frappe app/centrochange_core /home/frappe/frappe-bench/apps/centrochange_core

RUN uv pip install --no-cache --python /home/frappe/frappe-bench/env/bin/python --editable /home/frappe/frappe-bench/apps/centrochange_core \
    && printf '\n%s\n' centrochange_core >> sites/apps.txt \
    && bench build --app frappe --app erpnext --app builder --app healthcare --app centrochange_core
