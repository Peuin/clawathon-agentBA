# AI Business Analyst Agent - Deployment Guide

## GreenNode AgentBase Deployment

This guide covers deploying the AI Business Analyst Agent to GreenNode AgentBase platform.

---

## Prerequisites

| Requirement | Description |
|-------------|-------------|
| Docker | Installed on deployment machine |
| Supabase | PostgreSQL database running |
| OpenAI API | For LLM capabilities |

---

## Quick Start

### 1. Clone and Configure

```bash
cd business-analyst-agent

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### 2. Build Docker Image

```bash
# Build locally
docker build -t ai-business-analyst:latest .

# Or use docker-compose
docker-compose up --build
```

### 3. Test Locally

```bash
# Run container
docker run -p 8000:8000 --env-file .env ai-business-analyst:latest

# Test health endpoint
curl http://localhost:8000/health
```

---

## GreenNode AgentBase Deployment

### Option 1: Using agentbase-wizard

```bash
# Run the deployment wizard
/agentbase-wizard
```

### Option 2: Manual Deployment

1. **Build and push Docker image:**

```bash
# Tag for your registry
docker tag ai-business-analyst:latest your-registry/ai-business-analyst:v1.0.0

# Push to registry
docker push your-registry/ai-business-analyst:v1.0.0
```

2. **Deploy via AgentBase Console:**

- Navigate to AgentBase dashboard
- Create new "Custom Agent"
- Point to your Docker image
- Configure environment variables
- Deploy

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_ANON_KEY` | Yes | Supabase anonymous key |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Supabase service role key |
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `OPENAI_MODEL` | No | Model to use (default: gpt-4-turbo-preview) |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/projects` | GET/POST | List/Create projects |
| `/api/agent/chat` | POST | Chat with agent |
| `/api/integrations/jira` | POST | Sync to Jira |
| `/api/integrations/confluence` | POST | Publish to Confluence |
| `/api/integrations/gmail` | POST | Send sign-off email |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GreenNode AgentBase                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              AI Business Analyst Agent               │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │  FastAPI    │  │  LangGraph  │  │  System    │  │    │
│  │  │  Server     │  │  Workflow   │  │  Prompt    │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                    │                    │
                    ▼                    ▼
             ┌─────────────┐      ┌─────────────┐
             │  Supabase   │      │   OpenAI    │
             │  Database   │      │     LLM     │
             └─────────────┘      └─────────────┘
```

---

## Troubleshooting

### Container won't start

```bash
# Check logs
docker logs ai-business-analyst

# Verify .env file
docker run --rm --env-file .env ai-business-analyst:latest env
```

### Health check fails

```bash
# Test API directly
curl http://localhost:8000/health

# Check if port is exposed
docker port ai-business-analyst
```

---

## License

MIT
