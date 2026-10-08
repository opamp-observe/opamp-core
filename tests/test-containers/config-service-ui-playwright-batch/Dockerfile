FROM mcr.microsoft.com/playwright:v1.64.0-noble

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       python3 \
       python3-pip \
       python3-venv \
       git \
       curl \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY tests/test-containers/config-service-ui-playwright-batch/entrypoint.sh /usr/local/bin/run-config-service-playwright-batch
RUN sed -i 's/\r$//' /usr/local/bin/run-config-service-playwright-batch \
    && chmod +x /usr/local/bin/run-config-service-playwright-batch

ENTRYPOINT ["/usr/local/bin/run-config-service-playwright-batch"]
