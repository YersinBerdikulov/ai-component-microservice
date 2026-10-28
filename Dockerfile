# Multi-stage build:
#   base    - pinned runtime dependencies
#   test    - base + dev tools + tests (used by CI to lint and run pytest)
#   runtime - base + application code only, non-root, with a health check
# Build the production image with: docker build --target runtime -t ai-sim-service .

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt


FROM base AS test

COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

COPY pyproject.toml .
COPY app/ app/
COPY tests/ tests/

# LLM calls are mocked in the tests, no API keys needed
ENV DEFAULT_LLM_PROVIDER=openai

CMD ["pytest", "--junitxml=reports/junit.xml"]


FROM base AS runtime

# Numeric UID so Kubernetes can verify runAsNonRoot without resolving a user name
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin app \
    && mkdir -p data logs \
    && chown 10001:10001 data logs

COPY app/ app/

USER 10001

EXPOSE 8100

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8100/health', timeout=4)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]
