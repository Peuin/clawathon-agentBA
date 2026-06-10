"""
AI Business Analyst Agent - Workflow Controller
Using LangGraph for state machine management
"""

from typing import TypedDict, List, Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from datetime import date


# =============================================================================
# DATA MODELS
# =============================================================================

class ProjectContext(BaseModel):
    """Project context data"""
    name: str = ""
    description: str = ""
    business_need: str = ""
    stakeholders: List[str] = []
    as_is_state: str = ""
    to_be_state: str = ""


class RoadmapAnalysis(BaseModel):
    """Roadmap analysis data"""
    as_is_analysis: str = ""
    to_be_analysis: str = ""
    gaps: List[str] = []
    dependencies: List[str] = []
    risks: List[str] = []


class Milestone(BaseModel):
    """Milestone data"""
    name: str
    description: str = ""
    target_date: date
    status: str = "pending"


class Feature(BaseModel):
    """Feature data"""
    name: str
    description: str = ""
    priority: Literal["must-have", "should-have", "could-have", "won't-have"] = "should-have"
    status: str = "draft"
    acceptance_criteria: List[str] = []


class UIComponent(BaseModel):
    """UI component for wireframe"""
    type: Literal["text_field", "password_field", "button", "dropdown", "checkbox", "radio", "textarea", "table", "card", "header", "footer", "sidebar", "modal"]
    label: str = ""
    required: bool = False
    options: List[str] = []
    action: str = ""


class UIScreen(BaseModel):
    """UI screen structure"""
    screen_name: str
    components: List[UIComponent]


class UserStory(BaseModel):
    """User story data"""
    title: str
    as_a: str
    i_want: str
    so_that: str
    acceptance_criteria: List[str] = []
    priority: Literal["high", "medium", "low"] = "medium"
    status: str = "draft"


class TestCase(BaseModel):
    """Test case data"""
    title: str
    test_steps: List[str]
    expected_result: str
    priority: Literal["high", "medium", "low"] = "medium"
    status: str = "draft"


class ChangeRequest(BaseModel):
    """Change request data"""
    title: str
    description: str
    impact_analysis: str = ""
    status: Literal["pending", "approved", "rejected", "implemented"] = "pending"


# =============================================================================
# AGENT STATE
# =============================================================================

from typing import Annotated
from langgraph.graph import add_messages

class AgentState(TypedDict):
    """Main agent state"""
    # Session info
    session_id: Optional[str]
    project_id: Optional[str]
    current_step: int
    # Use Annotated for messages to handle multiple values
    messages: Annotated[list, add_messages]
    
    # Step data
    project_context: Optional[ProjectContext]
    roadmap_analysis: Optional[RoadmapAnalysis]
    milestones: List[Milestone]
    features: List[Feature]
    ui_screens: List[UIScreen]
    mermaid_diagrams: List[str]
    user_stories: List[UserStory]
    test_cases: List[TestCase]
    
    # Elicitation
    elicitation_questions: List[str]
    elicitation_answers: dict
    
    # Change requests
    change_requests: List[ChangeRequest]
    
    # Status
    status: Literal["active", "waiting_human", "completed", "paused"]
    pending_actions: List[str]
    messages: List[str]


# =============================================================================
# ELICITATION QUESTIONS BY STEP
# =============================================================================

ELICITATION_QUESTIONS = {
    1: [  # Project Context
        "What business problem or opportunity are you trying to address?",
        "Who are the key stakeholders involved in this project?",
        "What is the current process that needs to be improved?",
        "What constraints or requirements exist (budget, timeline, regulations)?",
    ],
    2: [  # Roadmap Analysis
        "What are the main pain points in the current process?",
        "What changes are expected in the target state?",
        "What are the critical dependencies between changes?",
        "What risks do you foresee?",
    ],
    3: [  # Timeline & Milestones
        "What is your target completion date?",
        "Are there any hard deadlines or regulatory dates to consider?",
        "How much effort can the team dedicate to this project?",
        "Are there any external dependencies that might affect the timeline?",
    ],
}


# =============================================================================
# WORKFLOW STEPS
# =============================================================================

class WorkflowSteps:
    STEP_NAMES = {
        1: "Project Context Analysis",
        2: "Roadmap Analysis",
        3: "Timeline & Milestones Proposal",
        4: "Feature Analysis",
        5: "UI Structure Generation",
        6: "Process Flow Generation",
        7: "Document Synthesis (BRD → FSD)",
        8: "User Stories Generation",
        9: "Test Cases Generation",
        10: "Delivery & Tracking",
    }


# =============================================================================
# WORKFLOW CONTROLLER
# =============================================================================

class BusinessAnalystWorkflow:
    """Main workflow controller using LangGraph"""
    
    def __init__(self, llm=None, db_client=None):
        self.llm = llm
        self.db_client = db_client
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine"""
        workflow = StateGraph(AgentState)
        
        # Add nodes for each step
        workflow.add_node("step_1", self.step_1_project_context)
        workflow.add_node("step_2", self.step_2_roadmap_analysis)
        workflow.add_node("step_3", self.step_3_timeline_milestones)
        workflow.add_node("step_4", self.step_4_feature_analysis)
        workflow.add_node("step_5", self.step_5_ui_generation)
        workflow.add_node("step_6", self.step_6_process_flow)
        workflow.add_node("step_7", self.step_7_document_synthesis)
        workflow.add_node("step_8", self.step_8_user_stories)
        workflow.add_node("step_9", self.step_9_test_cases)
        workflow.add_node("step_10", self.step_10_delivery)
        workflow.add_node("elicitation", self.handle_elicitation)
        workflow.add_node("change_request", self.handle_change_request)
        
        # Add edges
        workflow.set_entry_point("step_1")
        
        # Sequential flow with elicitation checks
        workflow.add_edge("step_1", "elicitation")
        workflow.add_edge("elicitation", "step_2")
        workflow.add_edge("step_2", "elicitation")
        workflow.add_edge("elicitation", "step_3")
        workflow.add_edge("step_3", "elicitation")
        workflow.add_edge("elicitation", "step_4")
        workflow.add_edge("step_4", "step_5")
        workflow.add_edge("step_5", "step_6")
        workflow.add_edge("step_6", "step_7")
        workflow.add_edge("step_7", "step_8")
        workflow.add_edge("step_8", "step_9")
        workflow.add_edge("step_9", "step_10")
        workflow.add_edge("step_10", END)
        
        return workflow.compile()
    
    # -------------------------------------------------------------------------
    # STEP HANDLERS
    # -------------------------------------------------------------------------
    
    def step_1_project_context(self, state: AgentState) -> AgentState:
        """Step 1: Project Context Analysis"""
        state["current_step"] = 1
        state["elicitation_questions"] = ELICITATION_QUESTIONS[1]
        state["messages"].append("Step 1: Let's analyze the project context.")
        return state
    
    def step_2_roadmap_analysis(self, state: AgentState) -> AgentState:
        """Step 2: Roadmap Analysis"""
        state["current_step"] = 2
        state["elicitation_questions"] = ELICITATION_QUESTIONS[2]
        state["messages"].append("Step 2: Analyzing the transformation path from As-Is to To-Be.")
        return state
    
    def step_3_timeline_milestones(self, state: AgentState) -> AgentState:
        """Step 3: Timeline & Milestones Proposal"""
        state["current_step"] = 3
        state["elicitation_questions"] = ELICITATION_QUESTIONS[3]
        state["messages"].append("Step 3: Proposing timeline and milestones.")
        return state
    
    def step_4_feature_analysis(self, state: AgentState) -> AgentState:
        """Step 4: Feature Analysis"""
        state["current_step"] = 4
        state["messages"].append("Step 4: Analyzing features in detail.")
        return state
    
    def step_5_ui_generation(self, state: AgentState) -> AgentState:
        """Step 5: UI Structure Generation"""
        state["current_step"] = 5
        state["messages"].append("Step 5: Generating UI wireframes.")
        return state
    
    def step_6_process_flow(self, state: AgentState) -> AgentState:
        """Step 6: Process Flow Generation"""
        state["current_step"] = 6
        state["messages"].append("Step 6: Generating BPMN process flows.")
        return state
    
    def step_7_document_synthesis(self, state: AgentState) -> AgentState:
        """Step 7: Document Synthesis"""
        state["current_step"] = 7
        state["messages"].append("Step 7: Synthesizing BRD and FSD documents.")
        return state
    
    def step_8_user_stories(self, state: AgentState) -> AgentState:
        """Step 8: User Stories Generation"""
        state["current_step"] = 8
        state["messages"].append("Step 8: Writing user stories.")
        return state
    
    def step_9_test_cases(self, state: AgentState) -> AgentState:
        """Step 9: Test Cases Generation"""
        state["current_step"] = 9
        state["messages"].append("Step 9: Writing test cases.")
        return state
    
    def step_10_delivery(self, state: AgentState) -> AgentState:
        """Step 10: Delivery & Tracking"""
        state["current_step"] = 10
        state["messages"].append("Step 10: Delivering and tracking progress.")
        return state
    
    # -------------------------------------------------------------------------
    # ELICITATION HANDLER
    # -------------------------------------------------------------------------
    
    def handle_elicitation(self, state: AgentState) -> AgentState:
        """Handle elicitation questions - ask human for input"""
        step = state["current_step"]
        questions = state.get("elicitation_questions", [])
        answers = state.get("elicitation_answers", {})
        
        # Check if all questions have been answered
        unanswered = [q for q in questions if q not in answers or not answers[q]]
        
        if unanswered:
            state["status"] = "waiting_human"
            state["pending_actions"] = unanswered
            # Return the first unanswered question
            state["messages"].append(f"Please answer: {unanswered[0]}")
        else:
            state["status"] = "active"
            state["pending_actions"] = []
            state["messages"].append("All questions answered. Proceeding to next step.")
        
        return state
    
    # -------------------------------------------------------------------------
    # CHANGE REQUEST HANDLER
    # -------------------------------------------------------------------------
    
    def handle_change_request(self, state: AgentState) -> AgentState:
        """Handle change request - update documents and create new versions"""
        state["messages"].append("Processing change request...")
        # The actual implementation would:
        # 1. Analyze impact
        # 2. Update affected documents
        # 3. Create new versions
        # 4. Return to the appropriate step
        return state
    
    # -------------------------------------------------------------------------
    # PUBLIC API
    # -------------------------------------------------------------------------
    
    def start_session(self, project_id: str) -> AgentState:
        """Start a new workflow session"""
        # Initialize with step 1
        state = self.step_1_project_context({
            "session_id": None,
            "project_id": project_id,
            "current_step": 1,
            "project_context": None,
            "roadmap_analysis": None,
            "milestones": [],
            "features": [],
            "ui_screens": [],
            "mermaid_diagrams": [],
            "user_stories": [],
            "test_cases": [],
            "elicitation_questions": [],
            "elicitation_answers": {},
            "change_requests": [],
            "status": "active",
            "pending_actions": [],
            "messages": [],
        })
        return state
    
    def process_message(self, state: AgentState, message: str) -> AgentState:
        """Process a message from the human"""
        # Store the answer if we're waiting for elicitation
        if state["status"] == "waiting_human" and state.get("pending_actions"):
            question = state["pending_actions"][0]
            answers = state["elicitation_answers"]
            answers[question] = message
            state["elicitation_answers"] = answers
            state["status"] = "active"
        
        # Simplified workflow - just advance step
        current_step = state.get("current_step", 1)
        
        # Move to next step after elicitation is complete
        if state.get("status") == "active" and current_step < 10:
            next_step = current_step + 1
            step_handlers = {
                1: self.step_1_project_context,
                2: self.step_2_roadmap_analysis,
                3: self.step_3_timeline_milestones,
                4: self.step_4_feature_analysis,
                5: self.step_5_ui_generation,
                6: self.step_6_process_flow,
                7: self.step_7_document_synthesis,
                8: self.step_8_user_stories,
                9: self.step_9_test_cases,
                10: self.step_10_delivery,
            }
            if next_step in step_handlers:
                state = step_handlers[next_step](state)
        
        # Add message to history
        state["messages"] = state.get("messages", []) + [message]
        
        return state
    
    def submit_change_request(self, state: AgentState, change: ChangeRequest) -> AgentState:
        """Submit a change request"""
        cr_list = state.get("change_requests", [])
        cr_list.append(change)
        state["change_requests"] = cr_list
        state["messages"].append(f"Change request submitted: {change.title}")
        return state


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

class DatabaseClient:
    """Supabase database client wrapper"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        from supabase import create_client
        self.client = create_client(supabase_url, supabase_key)
    
    def create_project(self, project: ProjectContext, user_id: str) -> dict:
        """Create a new project"""
        return self.client.table("projects").insert({
            "name": project.name,
            "description": project.description,
            "business_need": project.business_need,
            "stakeholders": project.stakeholders,
            "as_is_state": project.as_is_state,
            "to_be_state": project.to_be_state,
            "owner_id": user_id,
        }).execute()
    
    def create_milestone(self, project_id: str, milestone: Milestone) -> dict:
        """Create a milestone"""
        return self.client.table("milestones").insert({
            "project_id": project_id,
            "name": milestone.name,
            "description": milestone.description,
            "target_date": str(milestone.target_date),
            "status": milestone.status,
        }).execute()
    
    def create_feature(self, project_id: str, feature: Feature) -> dict:
        """Create a feature"""
        return self.client.table("features").insert({
            "project_id": project_id,
            "name": feature.name,
            "description": feature.description,
            "priority": feature.priority,
            "status": feature.status,
        }).execute()
    
    def create_user_story(self, feature_id: str, story: UserStory) -> dict:
        """Create a user story"""
        return self.client.table("user_stories").insert({
            "feature_id": feature_id,
            "title": story.title,
            "as_a": story.as_a,
            "i_want": story.i_want,
            "so_that": story.so_that,
            "acceptance_criteria": story.acceptance_criteria,
            "priority": story.priority,
            "status": story.status,
        }).execute()
    
    def create_document(self, project_id: str, doc_type: str, title: str, content: dict) -> dict:
        """Create a document"""
        return self.client.table("documents").insert({
            "project_id": project_id,
            "doc_type": doc_type,
            "title": title,
            "content": content,
        }).execute()
    
    def create_change_request(self, project_id: str, change: ChangeRequest, user_id: str) -> dict:
        """Create a change request"""
        return self.client.table("change_requests").insert({
            "project_id": project_id,
            "title": change.title,
            "description": change.description,
            "impact_analysis": change.impact_analysis,
            "requested_by": user_id,
            "status": change.status,
        }).execute()
    
    def update_document_version(self, document_id: str, content: dict) -> dict:
        """Update document and create new version"""
        return self.client.table("documents").update({
            "content": content,
        }).eq("id", document_id).execute()

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Example usage
    workflow = BusinessAnalystWorkflow()
    
    # Start a new session
    state = workflow.start_session("project-123")
    print(f"Started at step: {state['current_step']}")
    print(f"Questions: {state['elicitation_questions']}")
