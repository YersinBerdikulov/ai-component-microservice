# AI Simulator Service

[![CI/CD](../../actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue)
![License](https://img.shields.io/badge/license-MIT-green)

AI microservice for a digital simulator in which teachers practise **educational data analysis**.
It is part of a research project on developing teachers' data and visual literacy: the service
gives adaptive hints while a teacher works through a case scenario, predicts at-risk students,
grades code submissions, generates feedback reports, and logs every interaction for later
statistical analysis of the pilot study.

The main simulator backend (Spring Boot) calls this service over REST.

## Features

| Endpoint | Purpose | Technique |
|---|---|---|
| `POST /api/v1/assess-vl` | Placement test → visual-literacy level (beginner / intermediate / advanced) | Rule-based scoring |
| `POST /api/v1/predict` | Student dropout-risk prediction with top risk factors | scikit-learn RandomForest |
| `POST /api/v1/scaffold` | Adaptive hint for the current scenario step, adjusted to VL level | LLM |
| `POST /api/v1/chat` | Context-aware assistant chat with per-session history | LLM + Redis |
| `POST /api/v1/grade` | Grades a teacher's Python/SQL solution using its execution output | LLM (low temperature) |
| `POST /api/v1/report` | Feedback report on the teacher's decisions in a scenario | LLM |
| `GET /api/v1/pilot/stats` | Aggregated pilot-study metrics | — |
| `GET /api/v1/pilot/export` | Raw JSONL event log (`pd.read_json(..., lines=True)`) | — |
| `GET /health` | Liveness check | — |

Interactive API docs (Swagger UI) are served at `http://localhost:8100/docs`.

## Architecture

```
Spring Boot simulator ──REST──▶ FastAPI app
                                 ├── routers/      one module per endpoint
                                 ├── prompts/      prompt templates (Russian)
                                 ├── services/
                                 │    ├── llm_router   OpenAI | Anthropic | Gemini, chosen by env var
                                 │    ├── llm_cache    Redis cache of LLM answers (1 h TTL)
                                 │    ├── chat_history Redis chat memory (24 h TTL)
                                 │    └── pilot_logger JSONL event log for research data
                                 └── ml/predictor  RandomForest risk model
```

Design decisions:

- **Graceful degradation.** If Redis is unavailable, caching and chat history are skipped; the API
  keeps working. If the LLM returns malformed JSON, the endpoint falls back to the raw text instead of failing.
- **Provider-agnostic LLM layer.** Switching between OpenAI, Anthropic and Gemini is a single
  environment variable, which makes it possible to compare models in the study.
- **Reproducibility.** The risk model is trained on synthetic data with a fixed random seed, and all
  dependency versions are pinned.

## Technology choices

| Choice | Why |
|---|---|
| **Python 3.12** | Standard language for data science; the ML and LLM SDKs are Python-first. |
| **FastAPI** | Async (LLM calls are I/O-bound), automatic OpenAPI docs, request validation via Pydantic. Lighter than Django for a stateless microservice. |
| **Pydantic** | Typed request/response schemas give a clear contract with the Spring Boot backend. |
| **scikit-learn** | Mature, well-documented ML library; RandomForest handles mixed-scale features without normalisation and exposes feature importances for explanation. |
| **Redis** | In-memory store with TTLs, ideal for short-lived caches and chat sessions. |
| **Docker / Compose** | Same environment on every machine; one command starts the app with Redis. |
| **pytest + pytest-cov** | De-facto Python testing standard; LLM calls are mocked so tests are fast, free and deterministic. |
| **Ruff** | Very fast linter that replaces flake8 + isort + pyupgrade in one tool. |
| **GitHub Actions** | Built into GitHub, free for public repositories, needs no separate CI server. |

## Getting started

### Option 1 — Docker Compose (app + Redis)

```bash
cp .env.example .env        # add at least one LLM API key
docker compose up --build
```

### Option 2 — local Python

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --port 8100 --reload
```

The endpoints that don't call an LLM (`/health`, `/assess-vl`, `/predict`, `/pilot/*`) work without any API key.

### Configuration

| Variable | Default | Description |
|---|---|---|
| `DEFAULT_LLM_PROVIDER` | `openai` | `openai`, `anthropic` or `gemini` |
| `DEFAULT_MODEL` | provider-specific | Model name passed to the provider |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY` | — | Key for the chosen provider |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection |
| `PILOT_LOG_PATH` | `logs/pilot_events.jsonl` | Pilot-study event log |
| `LOG_LEVEL` | `INFO` | Python logging level |

## Testing

```bash
pytest --cov            # 33 tests, LLM calls are mocked, no API keys needed
ruff check app tests    # lint
```

Tests write pilot events to a temporary file, so they never touch the real research log.

## CI/CD

Pipeline: [`.github/workflows/ci.yml`](.github/workflows/ci.yml)

```
push / pull request
   │
   ▼
 lint ──▶ test (Python 3.12, 3.13 + Redis service) ──▶ docker build ──▶ smoke test ──▶ push to GHCR
          coverage + JUnit reports as artifacts                  (/health, /predict)   (push events only)
```

- **Continuous integration:** every push and pull request is linted and tested on two Python versions,
  with a real Redis service container.
- **Continuous delivery:** after the tests pass, the Docker image is built, started and checked with real
  HTTP requests. On pushes to the default branch and on `v*` tags, the image is published to
  GitHub Container Registry as `ghcr.io/<owner>/<repo>:latest`, `:<commit-sha>` and `:<tag>`.

## Project structure

```
app/
  main.py            FastAPI app, middleware, router registration
  routers/           HTTP endpoints
  services/          LLM router, caching, chat history, pilot logger, JSON helpers
  ml/predictor.py    risk model (trained on first use, saved to data/model.pkl)
  prompts/           LLM prompt templates
  models/schemas.py  Pydantic request/response models
tests/               pytest suite
.github/workflows/   CI/CD pipeline
```

## License

[MIT](LICENSE) © 2026 Yersin Berdikulov
