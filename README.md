# Replying Agent

**Replying Agent** is a FastAPI-based Facebook comment replying bot that uses Hugging Face inference endpoints to automatically reply to comments on Facebook posts. It is designed to be deployed as a webhook service that listens for new comments and generates relevant replies using AI.

## Features

- **Webhook Listener**: Receives and processes Facebook comment events via HTTP POST requests
- **AI-Powered Replies**: Generates replies using Hugging Face inference endpoints with support for multiple models
- **Background Processing**: Uses FastAPI's `BackgroundTasks` to handle long-running AI inference without blocking the webhook
- **Configuration Management**: Uses Pydantic settings for easy configuration of API keys, model IDs, and other parameters
- **Error Handling**: Graceful error handling for API failures with logging
- **Scalable Architecture**: Modular design with separate modules for configuration, ingestion, AI generation, and Facebook integration

## Prerequisites

- Python 3.8+
- pip (Python package installer)
- Hugging Face API token
- Facebook Page Access Token
- Facebook App with Webhook configured

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd replyingAgent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Create a `.env` file in the root directory with the following variables:

```env
HUGGINGFACE_TOKEN=your_huggingface_token_here
HUGGINGFACE_MODEL_ID=your_model_id_here
HUGGINGFACE_FALLBACK_MODEL_ID=your_fallback_model_id_here
HUGGINGFACE_MAX_NEW_TOKENS=256
HUGGINGFACE_TEMPERATURE=0.7
HUGGINGFACE_TOP_P=0.9
HUGGINGFACE_REQUEST_TIMEOUT=30

FB_TOKEN=your_facebook_token_here
FB_VERIFY_TOKEN=your_verify_token_here
FB_GRAPH_API_VERSION=v19.0
FB_GRAPH_API_BASE_URL=https://graph.facebook.com
FB_REQUEST_TIMEOUT=10
```

Alternatively, you can configure these in `config/config.yaml`.

## Usage

### Run the Server

Start the FastAPI server using `uvicorn`:

```bash
uvicorn main:app --reload
```

The server will start on `http://localhost:8000`.

### Configure Facebook Webhook

1. Get your public URL using ngrok:
   ```bash
   ngrok http 8000
   ```

2. In your Facebook App settings, configure the webhook with:
   - **Callback URL**: `https://your-ngrok-url.ngrok.io/trigger`
   - **Verify Token**: `facebookReplayBot` (or your configured verify token)
   - **Subscription Fields**: `comments`

### Trigger the Bot

Send a POST request to the `/trigger` endpoint with Facebook webhook data:

```bash
curl -X POST http://localhost:8000/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "object": "page",
    "entry": [
      {
        "id": "page_id",
        "time": 1776102717,
        "changes": [
          {
            "value": {
              "from": {
                "id": "sender_id",
                "name": "Sender Name"
              },
              "message": "Hello, how are you?",
              "comment_id": "comment_id",
              "post_id": "post_id"
            },
            "item": "comment",
            "verb": "add"
          }
        ]
      }
    ]
  }'
```

The bot will automatically generate a reply and post it to the comment.

## Project Structure

```
replyingAgent/
├── config/
│   ├── config.py          # Configuration management
│   ├── config.yaml        # Default configuration
│   └── serializers.py     # Pydantic serializers
├── src/
│   ├── facebook/
│   │   └── reply.py       # Facebook Graph API integration
│   ├── infrastructure/
│   │   └── hf_client.py   # Hugging Face client
│   ├── reply/
│   │   └── generate.py    # AI reply generation
│   └── utils/
│       └── ingestion.py   # Webhook data ingestion
├── main.py                # FastAPI application entry point
├── requirements.txt       # Project dependencies
├── .env                   # Environment variables (not in git)
└── README.md              # Project documentation
```

## API Endpoints

### `GET /`

**Description**: Health check endpoint

**Response**:
```json
{
  "Hello": "World"
}
```

### `GET /trigger`

**Description**: Verify Facebook webhook

**Query Parameters**:
- `hub.mode` (string, required): Webhook mode (should be "subscribe")
- `hub.verify_token` (string, required): Verification token
- `hub.challenge` (string, required): Challenge string

**Response**:
- `200 OK`: Returns the challenge string if verification succeeds
- `403 Forbidden`: If verification fails

### `POST /trigger`

**Description**: Process Facebook webhook events

**Request Body**:
```json
{
  "object": "page",
  "entry": [
    {
      "id": "page_id",
      "time": 1776102717,
      "changes": [
        {
          "value": {
            "from": {
              "id": "sender_id",
              "name": "Sender Name"
            },
            "message": "Comment text",
            "comment_id": "comment_id",
            "post_id": "post_id"
          },
          "item": "comment",
          "verb": "add"
        }
      ]
    }
  ]
}
```

**Response**:
```json
{
  "status": "ok"
}
```

## Development

### Testing

Run the development server with hot-reload:

```bash
uvicorn main:app --reload
```

### Adding New Models

To add a new Hugging Face model:

1. Update `config/config.yaml` with the new model ID:
   ```yaml
huggingface:
  model_id: "new-model-id"
  fallback_model_id: "your-fallback-model-id"
  # ... other settings
```

2. Ensure the new model is accessible via Hugging Face inference endpoints

3. Restart the server

### Webhook Configuration

When configuring the Facebook webhook, use a tool like ngrok to expose your local server to the internet:

```bash
ngrok http 8000
```

Copy the ngrok URL and use it as your webhook callback URL in Facebook settings.

## Deployment

For production deployment, consider using:

- Docker for containerization
- Gunicorn or Uvicorn with a production server
- A reverse proxy like Nginx
- Environment variables for configuration

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.