# FacebookReplay — AI-Powered Facebook Comment & Messenger Agent

A **FastAPI + LangGraph** service that listens to a Facebook webhook and automatically replies to:
- **Public comments** on Facebook posts (direct AI reply on the thread)
- **Private/sensitive comments** (a multilingual stub on the thread + a detailed DM via Messenger)
- **Messenger DMs** sent directly to the page

The AI backbone is **Hugging Face Inference API** with a primary/fallback model strategy. All configuration (prompts, model IDs, timeouts) lives in YAML files; secrets come from `.env`.

---

## Table of Contents
1. [Project Structure](#1-project-structure)
2. [Architecture Overview](#2-architecture-overview)
3. [LangGraph Pipeline](#3-langgraph-pipeline)
4. [Generators & AI Services](#4-generators--ai-services)
5. [Configuration System](#5-configuration-system)
6. [Environment Variables (.env)](#6-environment-variables-env)
7. [YAML Config Files](#7-yaml-config-files)
8. [API Endpoints](#8-api-endpoints)
9. [Infrastructure Clients](#9-infrastructure-clients)
10. [Running Locally](#10-running-locally)
11. [Key Design Decisions & Patterns](#11-key-design-decisions--patterns)
12. [Known TODOs & Future Work](#12-known-todos--future-work)

---

## 1. Project Structure

```
FacebookReplay/
├── main.py                         # FastAPI app entry point
├── Pipfile / Pipfile.lock          # Python 3.13 dependencies (pipenv)
├── .env                            # Secrets (not committed)
├── .env.dev                        # Dev-env overrides
│
├── config/                         # YAML configuration files (all merged at startup)
│   ├── prompt.yaml                 # reply + messenger system prompts
│   ├── classifierPrompt.yaml       # classifier system prompt
│   ├── facebookSettings.yaml       # graph_api_base_url, version, timeout
│   └── hfSettings.yaml             # model_id, fallback_model_id, max_new_tokens, temp, top_p
│
├── test.py                         # End-to-end mocked test script for the graph
│
└── app/
    ├── api/v1/
    │   ├── health.py               # GET /health
    │   └── webhock.py              # GET+POST /webhook (unified Facebook webhook)
    │
    ├── core/
    │   ├── settings_constant.py    # ConstantSettings — loads all YAML configs
    │   ├── settings_secrets.py     # SecretSettings — loads .env secrets
    │   └── serializers/
    │       ├── fb_settings.py      # FacebookSettings Pydantic model
    │       ├── hf_settings.py      # HuggingFaceSettings Pydantic model
    │       └── prompt.py           # Prompt Pydantic model (system_prompt field)
    │
    ├── features/
    │   ├── comments/
    │   │   ├── ingestion.py        # Parses raw Facebook webhook payload → (comment_id, text, sender_id)
    │   │   └── service.py          # reply() entry point → dispatches to LangGraph via background tasks
    │   └── messenger/
    │       ├── ingestion.py        # Parses Messenger webhook payload → (sender_id, text)
    │       └── service.py          # reply() entry point → generates & sends Messenger DM
    │
    ├── graph/
    │   ├── state.py                # CommentState (Pydantic BaseModel used by LangGraph)
    │   ├── builder.py              # Assembles & compiles the StateGraph (AgentGraph singleton)
    │   ├── router.py               # classification_router — routes public vs private
    │   └── nodes/
    │       ├── _helpers.py         # Shared utils: REPLY_DELAY_SECONDS, multilingual stubs, post_thread_reply()
    │       ├── classifier.py       # classifier_node — calls ClassifierGenerator
    │       ├── public_reply.py     # public_reply_node — generates & posts AI reply to comment thread
    │       └── private_reply.py    # private_reply_node — posts stub on thread + sends DM
    │
    ├── services/generator/
    │   ├── __init__.py             # Public re-exports for all generators
    │   ├── base_generator.py       # BaseReplyGenerator (ABC) — shared generate() pipeline
    │   └── generators/
    │       ├── facebook_comment_generator.py   # Public comment reply generator
    │       ├── messenger_reply_generator.py    # Messenger DM reply generator
    │       ├── private_reply_generator.py      # Detailed private reply (sent via DM)
    │       └── classifier_generator.py         # LLM-based classifier → returns (classification, language)
    │
    └── infrastructure/
        ├── facebook_client.py      # FacebookClient — wraps facebook-sdk + httpx for Messenger
        └── hf_client.py            # HFClient — async wrapper around huggingface_hub InferenceClient
```

---

## 2. Architecture Overview

```
Facebook Webhook (POST /webhook)
        │
        ▼
  webhock.py router
  ┌────────────────────────────────┐
  │  "messaging" in entry?         │
  │  → messenger/service.py        │
  │  "changes" in entry?           │
  │  → comments/service.py         │
  └────────────────────────────────┘
        │
        ▼
  comments/service.py
  ├── ingest_data() → [(comment_id, text, sender_id), ...]
  └── BackgroundTasks → process_cycle()
                              │
                              ▼
                     LangGraph Pipeline
                    (app/graph/builder.py)
```

---

## 3. LangGraph Pipeline

The graph is built once at module-import time as a **singleton** (`comment_graph = AgentGraph()`).

### State Schema (`CommentState` — Pydantic BaseModel)

| Field            | Type              | Description                                  |
|------------------|-------------------|----------------------------------------------|
| `comment_id`     | `str`             | Facebook comment/post ID                     |
| `sender_id`      | `str`             | Facebook user ID of the commenter            |
| `text`           | `str`             | Raw comment text                             |
| `history`        | `List[dict]`      | Conversation history (append-only via `add`) |
| `classification` | `Optional[str]`   | `"public"` or `"private"` (set by classifier)|
| `language`       | `Optional[str]`   | ISO-639-1 language code (default `"en"`)     |
| `next_node`      | `Optional[str]`   | Reserved for future routing overrides        |

### Graph Topology

```
START
  └─► classifier_node
          │
          ▼ (classification_router)
    ┌─────┴──────┐
    │            │
    ▼            ▼
public_reply  private_reply
  _node          _node
    │            │
    └─────┬──────┘
          ▼
         END
```

### Node Descriptions

| Node                | File                          | What it does                                                                                             |
|---------------------|-------------------------------|----------------------------------------------------------------------------------------------------------|
| `classifier_node`   | `nodes/classifier.py`         | Calls `ClassifierGenerator.classify()` → sets `classification` + `language` in state                    |
| `public_reply_node` | `nodes/public_reply.py`       | Generates AI reply via `facebook_comment_generator`, prepends `@[sender_id]`, posts to comment thread   |
| `private_reply_node`| `nodes/private_reply.py`      | Posts a multilingual stub on the thread, then sends a detailed DM via `facebook_client.send_messenger_message()` |

### Reply Delay
All thread replies go through `post_thread_reply()` in `_helpers.py`, which waits **20 seconds** (`REPLY_DELAY_SECONDS`) before posting to avoid an instant-bot feel.

### Checkpointer
Currently uses `MemorySaver` (in-process). The builder comment notes a future swap to `RedisSaver` for persistence and multi-tenant support.

---

## 4. Generators & AI Services

All generators inherit from `BaseReplyGenerator` (ABC) in `services/generator/base_generator.py`.

### BaseReplyGenerator

```python
class BaseReplyGenerator(ABC):
    def __init__(self, system_prompt: str, client: HFClient | None = None)
    def _format_user_message(self, user_input: str) -> str   # override to wrap input
    async def generate(self, user_input: str) -> str          # shared pipeline — do NOT override
```

The shared `generate()` always builds:
```python
messages = [
    {"role": "system", "content": self._system_prompt},
    {"role": "user",   "content": self._format_user_message(user_input)},
]
```

### Generator Singletons

| Singleton                     | Class                       | System Prompt Config Key | Purpose                                                    |
|-------------------------------|-----------------------------|---------------------------|------------------------------------------------------------|
| `facebook_comment_generator`  | `FacebookCommentGenerator`  | `constants.reply`         | Replies to public Facebook comments                        |
| `messenger_reply_generator`   | `MessengerReplyGenerator`   | `constants.messenger`     | Replies to Messenger DMs                                   |
| `private_reply_generator`     | `PrivateReplyGenerator`     | `constants.private_reply` | Detailed private reply sent as DM for classified comments  |
| `classifier_generator`        | `ClassifierGenerator`       | `constants.classifier`    | LLM-based classifier: returns `(classification, language)` |

### ClassifierGenerator Special Behavior
- Calls `generate()` with the raw comment text.
- Expects the LLM to return a JSON object like: `{"classification": "private", "language": "ar"}`
- Uses regex (`\{.*?\}` with `DOTALL`) to extract JSON even from markdown-fenced output.
- Falls back to `("public", "en")` on any parse failure.

---

## 5. Configuration System

Config is split into two classes, both using `pydantic-settings`:

### `ConstantSettings` (`app/core/settings_constant.py`)
Loads non-secret configuration from **all `.yaml` / `.yml` files** in the `config/` directory.

| Attribute     | Type                 | Source YAML File         |
|---------------|----------------------|--------------------------|
| `facebook`    | `FacebookSettings`   | `facebookSettings.yaml`  |
| `huggingface` | `HuggingFaceSettings`| `hfSettings.yaml`        |
| `reply`       | `Prompt`             | `prompt.yaml`            |
| `messenger`   | `Prompt`             | `prompt.yaml`            |
| `classifier`  | `Prompt`             | `classifierPrompt.yaml`  |
| `private_reply`| `Prompt`            | `classifierPrompt.yaml` or dedicated key |

Singleton: `constants = ConstantSettings()`

### `SecretSettings` (`app/core/settings_secrets.py`)
Loads secrets from `.env` file.

| Field           | Env Variable       | Description                    |
|-----------------|--------------------|--------------------------------|
| `hf_token`      | `HF_TOKEN`         | Hugging Face API token         |
| `fb_token`      | `FB_TOKEN`         | Facebook Page Access Token     |
| `fb_verify_token`| `FB_VERIFY_TOKEN` | Facebook webhook verify token  |

Singleton: `secrets = SecretSettings()`

---

## 6. Environment Variables (.env)

Create a `.env` file in the project root with:

```env
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
FB_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FB_VERIFY_TOKEN=your_custom_verify_token
```

> **Railway / Production**: Set these as environment variables in your deployment platform dashboard. The app will automatically pick them up since `SecretSettings` reads from both `.env` and OS environment.

---

## 7. YAML Config Files

### `config/facebookSettings.yaml`
```yaml
facebook:
  graph_api_base_url: https://graph.facebook.com
  graph_api_version: v19.0
  request_timeout: 30
```

### `config/hfSettings.yaml`
```yaml
huggingface:
  model_id: mistralai/Mistral-7B-Instruct-v0.3    # Primary model
  fallback_model_id: HuggingFaceH4/zephyr-7b-beta  # Used if primary fails
  max_new_tokens: 512
  temperature: 0.7
  top_p: 0.9
```

### `config/prompt.yaml`
```yaml
reply:
  system_prompt: >
    You are a helpful customer support assistant for Satalitor...
    (Reply to public Facebook comments)

messenger:
  system_prompt: >
    You are a helpful customer support assistant for Satalitor...
    (Reply to Messenger DMs)
```

### `config/classifierPrompt.yaml`
```yaml
classifier:
  system_prompt: >
    Classify the comment as "public" or "private"...
    Return JSON: {"classification": "...", "language": "..."}

private_reply:
  system_prompt: >
    You are replying privately to a user who needs detailed assistance...
```

---

## 8. API Endpoints

### `GET /health`
Simple health check. Returns `200 OK`.

### `GET /webhook/`
Facebook webhook verification endpoint.

| Query Param       | Expected Value              |
|-------------------|-----------------------------|
| `hub.mode`        | `subscribe`                 |
| `hub.verify_token`| Matches `FB_VERIFY_TOKEN`   |
| `hub.challenge`   | Any string (echoed back)    |

### `POST /webhook/`
Unified event listener. Detects event type from payload:

| Condition               | Routed To              |
|-------------------------|------------------------|
| `"messaging"` in entry  | `messenger/service.py` |
| `"changes"` in entry    | `comments/service.py`  |

Always returns `{"status": "ok"}` immediately; heavy work runs in background tasks.

---

## 9. Infrastructure Clients

### `HFClient` (`app/infrastructure/hf_client.py`)
- Wraps `huggingface_hub.InferenceClient` for async chat completion.
- Uses `provider="auto"` — HF picks the best available inference provider.
- Primary/fallback model strategy: tries `model_id` first, falls back to `fallback_model_id`.
- All calls use `asyncio.to_thread()` to keep FastAPI async-safe.

Singleton: `hf_client = HFClient()`

### `FacebookClient` (`app/infrastructure/facebook_client.py`)
- `post_reply(comment_id, reply_text)` — posts to a comment thread via `facebook-sdk` GraphAPI (thread-offloaded to async).
- `send_messenger_message(recipient_id, text)` — sends a Messenger DM via direct `httpx` POST to `/{version}/me/messages` (facebook-sdk only supports up to v3.1 for Messenger).

Singleton: `facebook_client = FacebookClient()`

---

## 10. Running Locally

### Prerequisites
- Python 3.13
- `pipenv`

### Setup

```bash
# Install dependencies
pipenv install

# Activate virtual environment
pipenv shell

# Create .env with your secrets (see Section 6)

# Run the dev server
uvicorn main:app --reload --port 8000
```

### Exposing Locally for Facebook Webhook (ngrok)
Facebook requires a public HTTPS URL for webhook verification.

```bash
ngrok http 8000
# Copy the https:// URL → set as webhook URL in Facebook App Dashboard
```

### Running the Test Script
```bash
python test.py
```
The test script mocks the HF client and Facebook client to validate the entire LangGraph orchestration flow without real API calls.

---

## 11. Key Design Decisions & Patterns

### Singleton Pattern
All heavy objects (graph, clients, generators) are instantiated once at module import time and reused across requests. This avoids re-initialization overhead per request.

### Abstract Generator Pattern
`BaseReplyGenerator` enforces that all generators share the same `generate()` pipeline. Adding a new generator (e.g., for WhatsApp) only requires:
1. Subclassing `BaseReplyGenerator`
2. Passing the correct `system_prompt`
3. Optionally overriding `_format_user_message()`

### Config Separation (Secrets vs Constants)
- **Secrets** (tokens, keys) → `.env` file via `SecretSettings`
- **Constants** (prompts, model IDs, timeouts) → YAML files via `ConstantSettings`

This makes it safe to commit YAML configs to Git while keeping secrets out.

### YAML Auto-Merge
`ConstantSettings` merges **all** YAML files in `config/` at startup. Adding a new config category just requires creating a new YAML file — no code changes needed.

### Background Tasks
Comment processing runs as FastAPI `BackgroundTasks`. The webhook returns `{"status": "ok"}` immediately to Facebook (within the required 5-second window), then processes asynchronously.

### Comment Classification Flow
The `ClassifierGenerator` uses the LLM itself to classify comments as `public` or `private`. Private comments are those that require personal/sensitive handling (e.g., pricing, complaints, account issues). The LLM returns structured JSON for reliable parsing.

### Private Reply Flow
1. Post a brief multilingual stub on the public comment thread (e.g., "Replied privately" / "تم الرد بشكل خاص")
2. Generate a detailed AI response
3. Send it via Messenger DM to the commenter's `sender_id`

---

## 12. Known TODOs & Future Work

- [ ] **Swap `MemorySaver` → `RedisSaver`** for persistent multi-session conversation history (noted in `builder.py`)
- [ ] **Redis short-term memory** for conversation history across turns (noted in past LangGraph design)
- [ ] **Arize Phoenix / OpenTelemetry** observability integration (planned in LangGraph multi-tenant design)
- [ ] **Human-in-the-loop overrides** for high-priority or emotional comments (e.g., "Mad" emotion routing)
- [ ] **Emotion detection node** — add an emotion classification step to the LangGraph pipeline
- [ ] **RAG integration** — connect to a product/policy knowledge base for grounded answers
- [ ] **Production deployment** — Railway platform with env vars (setup previously done)
- [ ] Fix typo: `webhock.py` → `webhook.py`