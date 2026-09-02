FROM frappe/erpnext:v16.32.0

# Builder master at this pinned commit declares Frappe >=15,<18 compatibility.
ARG BUILDER_REF=41987c064da4650e6901b5da82b7c76add452ebf

USER frappe
WORKDIR /home/frappe/frappe-bench

RUN bench get-app --branch master builder https://github.com/frappe/builder.git \
    && git -C apps/builder checkout "${BUILDER_REF}"

COPY --chown=frappe:frappe app/centrochange_core /home/frappe/frappe-bench/apps/centrochange_core

RUN uv pip install --no-cache --python /home/frappe/frappe-bench/env/bin/python --editable /home/frappe/frappe-bench/apps/centrochange_core \
    && printf '\n%s\n' centrochange_core >> sites/apps.txt \
    && bench build --app builder --app centrochange_core
