FROM mcr.microsoft.com/playwright:v1.58.2-noble@sha256:6446946a1d9fd62d9ae501312a2d76a43ee688542b21622056a372959b65d63d
WORKDIR /qa
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY flows.cjs public.cjs finance.cjs threshold.cjs uat.cjs professional.cjs patient.cjs ./
