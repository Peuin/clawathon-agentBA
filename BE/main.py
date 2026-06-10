"""
AI Business Analyst Agent - FastAPI Entry Point
"""

import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from langchain_openai import ChatOpenAI

from workflow_controller import (
    BusinessAnalystWorkflow,
    DatabaseClient,
    ProjectContext,
    Milestone,
    Feature,
    UserStory,
    TestCase,
    ChangeRequest,
)

app = FastAPI(title="AI Business Analyst Agent", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# LLM Configuration (GreenNode)
# =============================================================================
def get_llm():
    """Initialize LLM with GreenNode configuration"""
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL", "https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1")
    model = os.getenv("LLM_MODEL", "qwen/qwen3-5-27b")
    
    if not api_key:
        return None
    
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=0.7,
        max_tokens=4000,
    )


# Initialize clients
def get_db_client():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if supabase_url and supabase_key:
        return DatabaseClient(supabase_url, supabase_key)
    return None

def get_workflow(llm=None):
    """Get workflow instance with LLM"""
    return BusinessAnalystWorkflow(llm=llm)

# In-memory storage for demo (replace with Supabase in production)
projects_store = {}
documents_store = {}
diagrams_store = {}
agent_sessions = {}

# =============================================================================
# MODELS
# =============================================================================

class ChatRequest(BaseModel):
    project_id: str
    message: str
    history: list = []

class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    business_need: str = ""
    stakeholders: list = []

class MilestoneCreate(BaseModel):
    project_id: str
    name: str
    description: str = ""
    target_date: str

class FeatureCreate(BaseModel):
    project_id: str
    name: str
    description: str = ""
    priority: str = "should-have"

class UserStoryCreate(BaseModel):
    feature_id: str
    title: str
    as_a: str
    i_want: str
    so_that: str
    acceptance_criteria: list = []
    priority: str = "medium"

class DocumentCreate(BaseModel):
    project_id: str
    title: str
    doc_type: str
    content: str

class ChangeRequestCreate(BaseModel):
    project_id: str
    title: str
    description: str

# =============================================================================
# API ROUTES
# =============================================================================

@app.get("/")
async def root():
    return {"message": "AI Business Analyst Agent API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# -------------------------------------------------------------------------
# Projects
# -------------------------------------------------------------------------

@app.get("/api/projects")
async def list_projects():
    """List all projects"""
    return list(projects_store.values())

@app.post("/api/projects")
async def create_project(project: ProjectCreate):
    """Create a new project"""
    project_id = f"proj_{len(projects_store) + 1}"
    project_data = {
        "id": project_id,
        "name": project.name,
        "description": project.description,
        "business_need": project.business_need,
        "stakeholders": project.stakeholders,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    projects_store[project_id] = project_data
    return project_data

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get project by ID"""
    if project_id not in projects_store:
        raise HTTPException(status_code=404, detail="Project not found")
    return projects_store[project_id]

@app.get("/api/projects/{project_id}/documents")
async def list_documents(project_id: str):
    """List documents for a project"""
    docs = [d for d in documents_store.values() if d.get("project_id") == project_id]
    return docs

@app.get("/api/projects/{project_id}/diagrams")
async def list_diagrams(project_id: str):
    """List diagrams for a project"""
    diagrams = [d for d in diagrams_store.values() if d.get("project_id") == project_id]
    return diagrams

# -------------------------------------------------------------------------
# Agent Chat
# -------------------------------------------------------------------------

@app.post("/api/agent/chat")
async def chat(request: ChatRequest):
    """Send message to the agent"""
    project_id = request.project_id
    
    # Get LLM instance
    llm = get_llm()
    
    # Get or create agent session
    if project_id not in agent_sessions:
        workflow = get_workflow(llm=llm)
        state = workflow.start_session(project_id)
        agent_sessions[project_id] = state
    else:
        state = agent_sessions[project_id]
    
    # Process message through workflow
    workflow = get_workflow(llm=llm)
    state = workflow.process_message(state, request.message)
    
    # Update session
    agent_sessions[project_id] = state
    
    # Generate response based on current step
    current_step = state.get("current_step", 1)
    step_names = {
        1: "Project Context Analysis",
        2: "Roadmap Analysis", 
        3: "Timeline & Milestones",
        4: "Feature Analysis",
        5: "UI Structure Generation",
        6: "Process Flow Generation",
        7: "Document Synthesis",
        8: "User Stories Generation",
        9: "Test Cases Generation",
        10: "Delivery & Tracking",
    }
    
    step_name = step_names.get(current_step, "Unknown")
    
    # Generate response based on step
    response = generate_agent_response(state, request.message)
    
    return {
        "response": response,
        "current_step": current_step,
        "step_name": step_name,
        "status": state.get("status", "active"),
    }

def generate_agent_response(state, user_message):
    """Generate agent response based on current state"""
    current_step = state.get("current_step", 1)
    elicitation_answers = state.get("elicitation_answers", {})
    
    if state.get("status") == "waiting_human":
        pending = state.get("pending_actions", [])
        if pending:
            return pending[0]
    
    # Step-based responses
    responses = {
        1: """Great! Now let's move to **Step 2: Roadmap Analysis**.

To understand the transformation path, I'd like to ask:

1. What are the main pain points in the current process?
2. What changes are expected in the target state?
3. What are the critical dependencies between changes?

Please share your thoughts on these questions.""",
        
        2: """Excellent! Now let's proceed to **Step 3: Timeline & Milestones**.

Based on the context gathered, let's discuss the timeline:

1. What is your target completion date?
2. Are there any hard deadlines or regulatory dates to consider?
3. How much effort can the team dedicate to this project?

Please provide your availability and constraints.""",
        
        3: """Perfect! Now let's move to **Step 4: Feature Analysis**.

Based on your inputs, let's identify the key features:

1. What specific functionality is needed?
2. What are the must-have vs nice-to-have features?
3. How should features be prioritized?

Please describe the features you'd like to include.""",
        
        4: """Great progress! Now let's move to **Step 5: UI Structure Generation**.

I'll generate UI wireframes based on the features we've identified. 

In the meantime, would you like me to:
- Generate the UI structure in JSON format?
- Proceed to Step 6 for process flows?

Let me know your preference.""",
        
        5: """Now let's move to **Step 6: Process Flow Generation**.

I'll generate BPMN diagrams to visualize the workflows. 

Would you like me to:
- Generate a process flow diagram using Mermaid.js?
- Proceed to Step 7 for document synthesis?

Please confirm your preference.""",
        
        6: """Excellent! Now let's move to **Step 7: Document Synthesis**.

I'll synthesize all the information into BRD and FSD documents.

The documents will include:
- Business context and objectives
- Feature specifications
- UI wireframes
- Process flows
- User stories

Shall I proceed with generating the documents?""",
        
        7: """Great! Now let's move to **Step 8: User Stories Generation**.

I'll create user stories in the "As a... I want... So that..." format with acceptance criteria.

Each user story will include:
- Role, action, and benefit
- Acceptance criteria (Given/When/Then)
- Priority level

Shall I generate the user stories?""",
        
        8: """Perfect! Now let's move to **Step 9: Test Cases Generation**.

I'll generate test cases for each user story.

Each test case will include:
- Test title and description
- Test steps
- Expected results
- Priority

Shall I generate the test cases?""",
        
        9: """Excellent! Now let's move to **Step 10: Delivery & Tracking**.

At this step, I can help you:
- **Sync to Jira**: Push user stories as Jira issues
- **Publish to Confluence**: Upload BRD/FSD documents
- **Send Sign-off Email**: Email summary to stakeholders

What would you like me to do first?""",
        
        10: """Great! The analysis is complete. 

You can:
- Review all documents in the Document tab
- View diagrams in the Canvas tab
- Use action buttons to sync with Jira, Confluence, or send emails

Would you like to make any changes or start a new analysis?""",
    }
    
    return responses.get(current_step, "How can I help you further with your project?")

# -------------------------------------------------------------------------
# Milestones
# -------------------------------------------------------------------------

@app.post("/api/milestones")
async def create_milestone(milestone: MilestoneCreate):
    """Create a milestone"""
    milestone_id = f"mile_{len(projects_store) + 1}"
    milestone_data = {
        "id": milestone_id,
        "project_id": milestone.project_id,
        "name": milestone.name,
        "description": milestone.description,
        "target_date": milestone.target_date,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
    }
    return milestone_data

# -------------------------------------------------------------------------
# Features
# -------------------------------------------------------------------------

@app.post("/api/features")
async def create_feature(feature: FeatureCreate):
    """Create a feature"""
    feature_id = f"feat_{len(projects_store) + 1}"
    feature_data = {
        "id": feature_id,
        "project_id": feature.project_id,
        "name": feature.name,
        "description": feature.description,
        "priority": feature.priority,
        "status": "draft",
        "created_at": datetime.now().isoformat(),
    }
    return feature_data

# -------------------------------------------------------------------------
# User Stories
# -------------------------------------------------------------------------

@app.post("/api/user-stories")
async def create_user_story(story: UserStoryCreate):
    """Create a user story"""
    story_id = f"story_{len(projects_store) + 1}"
    story_data = {
        "id": story_id,
        "feature_id": story.feature_id,
        "title": story.title,
        "as_a": story.as_a,
        "i_want": story.i_want,
        "so_that": story.so_that,
        "acceptance_criteria": story.acceptance_criteria,
        "priority": story.priority,
        "status": "draft",
        "created_at": datetime.now().isoformat(),
    }
    return story_data

# -------------------------------------------------------------------------
# Documents
# -------------------------------------------------------------------------

@app.post("/api/documents")
async def create_document(doc: DocumentCreate):
    """Create a document"""
    doc_id = f"doc_{len(documents_store) + 1}"
    doc_data = {
        "id": doc_id,
        "project_id": doc.project_id,
        "title": doc.title,
        "doc_type": doc.doc_type,
        "content": doc.content,
        "current_version": 1,
        "status": "draft",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    documents_store[doc_id] = doc_data
    return doc_data

@app.get("/api/documents/{doc_id}/versions")
async def list_document_versions(doc_id: str):
    """List document versions"""
    # Mock versions
    return [
        {"id": "1", "version_number": 2, "created_at": "2024-01-15", "change_summary": "Updated acceptance criteria"},
        {"id": "2", "version_number": 1, "created_at": "2024-01-10", "change_summary": "Initial version"},
    ]

# -------------------------------------------------------------------------
# Change Requests
# -------------------------------------------------------------------------

@app.post("/api/change-requests")
async def create_change_request(cr: ChangeRequestCreate):
    """Create a change request"""
    cr_id = f"cr_{len(projects_store) + 1}"
    cr_data = {
        "id": cr_id,
        "project_id": cr.project_id,
        "title": cr.title,
        "description": cr.description,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
    }
    return cr_data

# -------------------------------------------------------------------------
# Integrations (placeholder - implement with direct API calls)
# -------------------------------------------------------------------------

@app.post("/api/integrations/jira/sync")
async def sync_to_jira():
    """Sync user stories to Jira"""
    return {"success": True, "message": "Jira integration not configured"}

@app.post("/api/integrations/confluence/publish")
async def publish_to_confluence():
    """Publish documents to Confluence"""
    return {"success": True, "message": "Confluence integration not configured"}

@app.post("/api/integrations/gmail/send-signoff")
async def send_signoff_email():
    """Send sign-off email"""
    return {"success": True, "message": "Gmail integration not configured"}


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)