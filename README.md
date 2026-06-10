# 🤖 AI Business Analyst Agent

An AI-powered Business Analyst Agent following BABOK v3 methodology, deployable to GreenNode AgentBase.

## 📋 Overview

This agent assists Business Analysts in managing the complete requirements lifecycle:

- **Project Context Analysis** - Business needs, stakeholders identification
- **Roadmap Planning** - As-Is & To-Be analysis
- **Timeline & Milestones** - Interactive planning with human validation
- **Feature Analysis** - Detailed feature breakdown
- **UI Wireframing** - AI-generated UI mockups rendered on canvas
- **Process Modeling** - BPMN/Flowchart generation with Mermaid.js
- **Documentation** - BRD, FSD generation with version control
- **User Stories** - Acceptance Criteria writing
- **Test Cases** - Test scenario creation
- **Delivery Tracking** - Progress monitoring

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                       │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ Sidebar  │  │ Chat Interface│  │ AI Canvas (Mermaid)│   │
│  └──────────┘  └──────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Server (Port 8000)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────────┐  │
│  │  REST API   │  │ LangGraph   │  │  System Prompt     │  │
│  │  Endpoints  │  │  Workflow   │  │  (BABOK v3)        │  │
│  └─────────────┘  └─────────────┘  └────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                    │                    │
                    ▼                    ▼
             ┌─────────────┐      ┌─────────────┐
             │  Supabase   │      │   OpenAI    │
             │  Database   │      │     LLM     │
             └─────────────┘      └─────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase account
- OpenAI API key

### Backend Setup

```bash
cd business-analyst-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run server
python main.py
```

### Frontend Setup

```bash
cd frontend/ai-ba-copilot

# Install dependencies
npm install

# Run development server
npm run dev

# Open http://localhost:3003
```

## 📁 Project Structure

```
claw-a-thon-peuin-demo/
├── business-analyst-agent/
│   ├── main.py                 # FastAPI entry point
│   ├── workflow_controller.py  # LangGraph state machine
│   ├── system_prompt.md        # Agent system prompt
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile              # Docker image definition
│   ├── docker-compose.yml      # Docker compose config
│   ├── .env.example            # Environment template
│   └── DEPLOY.md               # Deployment guide
│
├── frontend/
│   └── ai-ba-copilot/
│       ├── src/
│       │   ├── app/            # Next.js app router
│       │   ├── components/     # React components
│       │   └── lib/            # Utilities
│       └── package.json
│
├── supabase/
│   └── schema.sql              # Database schema + RLS
│
└── greennode-agentbase-skills/  # GreenNode deployment skills
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/projects` | GET | List all projects |
| `/api/projects` | POST | Create new project |
| `/api/agent/chat` | POST | Chat with AI BA |
| `/api/integrations/jira` | POST | Create Jira issues |
| `/api/integrations/confluence` | POST | Publish to Confluence |
| `/api/integrations/gmail` | POST | Send sign-off email |

## 🐳 Docker Deployment

### Build

```bash
cd business-analyst-agent
docker build -t ai-business-analyst:latest .
```

### Run

```bash
docker run -p 8000:8000 --env-file .env ai-business-analyst:latest
```

### Docker Compose

```bash
docker-compose up --build
```

## 📊 Database Schema

Tables:
- `projects` - Project information
- `milestones` - Project milestones & timelines
- `features` - Feature definitions
- `user_stories` - User stories with acceptance criteria
- `documents` - BRD, FSD documents
- `document_versions` - Version history
- `change_requests` - Change request tracking
- `test_cases` - Test case definitions
- `agent_sessions` - Session management
- `api_integrations` - Integration configs

## 🤝 Integrations

### Jira
- Create Epic/Task/Story
- Update issue status

### Confluence
- Create/Update pages
- Publish documentation

### Gmail
- Send sign-off emails
- Attach document links

## 📝 License

MIT
