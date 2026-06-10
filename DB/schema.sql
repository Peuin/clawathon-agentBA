-- =============================================================================
-- AI Business Analyst Agent - Supabase Database Schema
-- Based on BABOK v3 standards
-- =============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- 1. PROJECTS TABLE
-- =============================================================================
CREATE TABLE public.projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    business_need TEXT,
    stakeholders JSONB DEFAULT '[]'::jsonb,
    as_is_state TEXT,
    to_be_state TEXT,
    status VARCHAR(50) DEFAULT 'planning'::varchar,
    owner_id UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS for projects
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view projects they own or are members of"
    ON public.projects FOR SELECT
    USING (owner_id = auth.uid() OR 
           auth.uid() IN (SELECT jsonb_array_elements_text(stakeholders::jsonb))::UUID);

CREATE POLICY "Users can insert their own projects"
    ON public.projects FOR INSERT
    WITH CHECK (owner_id = auth.uid());

CREATE POLICY "Users can update their own projects"
    ON public.projects FOR UPDATE
    USING (owner_id = auth.uid());

CREATE POLICY "Users can delete their own projects"
    ON public.projects FOR DELETE
    USING (owner_id = auth.uid());

-- =============================================================================
-- 2. MILESTONES TABLE
-- =============================================================================
CREATE TABLE public.milestones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    target_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending'::varchar,
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS for milestones
ALTER TABLE public.milestones ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view milestones of their projects"
    ON public.milestones FOR SELECT
    USING (
        project_id IN (
            SELECT id FROM public.projects 
            WHERE owner_id = auth.uid() 
            OR auth.uid() IN (SELECT jsonb_array_elements_text(stakeholders::jsonb))::UUID
        )
    );

CREATE POLICY "Users can insert milestones for their projects"
    ON public.milestones FOR INSERT
    WITH CHECK (
        project_id IN (
            SELECT id FROM public.projects WHERE owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can update milestones for their projects"
    ON public.milestones FOR UPDATE
    USING (
        project_id IN (
            SELECT id FROM public.projects WHERE owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete milestones for their projects"
    ON public.milestones FOR DELETE
    USING (
        project_id IN (
            SELECT id FROM public.projects WHERE owner_id = auth.uid()
        )
    );

-- =============================================================================
-- 3. FEATURES TABLE
-- =============================================================================
CREATE TABLE public.features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    milestone_id UUID REFERENCES public.milestones(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    priority VARCHAR(50) DEFAULT 'medium'::varchar,
    status VARCHAR(50) DEFAULT 'draft'::varchar,
    jira_epic_key VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS for features
ALTER TABLE public.features ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view features of their projects"
    ON public.features FOR SELECT
    USING (
        project_id IN (
            SELECT id FROM public.projects 
            WHERE owner_id = auth.uid() 
            OR auth.uid() IN (SELECT jsonb_array_elements_text(stakeholders::jsonb))::UUID
        )
    );

CREATE POLICY "Users can insert features for their projects"
    ON public.features FOR INSERT
    WITH CHECK (
        project_id IN (
            SELECT id FROM public.projects WHERE owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can update features for their projects"
    ON public.features FOR UPDATE
    USING (
        project_id IN (
            SELECT id FROM public.projects WHERE owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete features for their projects"
    ON public.features FOR DELETE
    USING (
        project_id IN (
            SELECT id FROM public.projects WHERE owner_id = auth.uid()
        )
    );

-- =============================================================================
-- 4. USER STORIES TABLE
-- =============================================================================
CREATE TABLE public.user_stories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    feature_id UUID NOT NULL REFERENCES public.features(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    as_a VARCHAR(255),
    i_want TEXT,
    so_that TEXT,
    acceptance_criteria JSONB DEFAULT '[]'::jsonb,
    priority VARCHAR(50) DEFAULT 'medium'::varchar,
    status VARCHAR(50) DEFAULT 'draft'::varchar,
    jira_story_key VARCHAR(100),
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS for user_stories
ALTER TABLE public.user_stories ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view user stories of their projects"
    ON public.user_stories FOR SELECT
    USING (
        feature_id IN (
            SELECT id FROM public.features
            WHERE project_id IN (
                SELECT id FROM public.projects 
                WHERE owner_id = auth.uid() 
                OR auth.uid() IN (SELECT jsonb_array_elements_text(stakeholders::jsonb))::UUID
            )
        )
    );

CREATE POLICY "Users can insert user stories for their projects"
    ON public.user_stories FOR INSERT
    WITH CHECK (
        feature_id IN (
            SELECT id FROM public.features
            WHERE project_id IN (
                SELECT id FROM public.projects WHERE owner_id = auth.uid()
            )
        )
    );

CREATE POLICY "Users can update user stories for their projects"
    ON public.user_stories FOR UPDATE
    USING (
        feature_id IN (
            SELECT id FROM public.features
            WHERE project_id IN (
                SELECT id FROM public.projects WHERE owner_id = auth.uid()
            )
        )
    );

CREATE POLICY "Users can delete user stories for their projects"
    ON public.user_stories FOR DELETE
    USING (
        feature_id IN (
            SELECT id FROM public.features
            WHERE project_id IN (
                SELECT id FROM public.projects WHERE owner_id = auth.uid()
            )
        )
    );

-- =============================================================================
-- 5. DOCUMENTS TABLE (with Version Control)
-- =============================================================================
CREATE TABLE public.documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    doc_type VARCHAR(50) NOT NULL, -- 'BRD', 'FSD', 'TEST_CASE', 'OTHER'
    content JSONB DEFAULT '{}'::jsonb,
    current_version INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'draft'::varchar,
    confluence_page_id VARCHAR(100),
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS for documents
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view documents of their projects"
    ON public.documents FOR SELECT
    USING (
        project_id IN (
            SELECT id FROM public.projects 
            WHERE owner_id = auth.uid() 
            OR auth.uid() IN (SELECT jsonb_array_elements_text(stakeholders::jsonb))::UUID
        )
    );

CREATE POLICY "Users can insert documents for their projects"
    ON public.documents FOR INSERT
    WITH CHECK (
        project_id IN (
            SELECT id FROM public.projects WHERE owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can update documents for their projects"
    ON public.documents FOR UPDATE
    USING (
        project_id IN (
            SELECT id FROM public.projects WHERE owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete documents for their projects"
    ON public.documents FOR DELETE
    USING (
        project_id IN (
            SELECT id FROM public.projects WHERE owner_id = auth.uid()
        )
    );

-- =============================================================================
-- 6. DOCUMENT VERSIONS TABLE (History Tracking)
-- =============================================================================
CREATE TABLE public.document_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    content JSONB NOT NULL,
    change_summary TEXT,
    changed_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS for document_versions
ALTER TABLE public.document_versions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view document versions of their projects"
    ON public.document_versions FOR SELECT
    USING (
        document_id IN (
            SELECT id FROM public.documents
            WHERE project_id IN (
                SELECT id FROM public.projects 
                WHERE owner_id = auth.uid() 
                OR auth.uid() IN (SELECT jsonb_array_elements_text(stakeholders::jsonb))::UUID
            )
        )
    );

CREATE POLICY "Users can insert document versions for their projects"
    ON public.document_versions FOR INSERT
    WITH CHECK (
        document_id IN (
            SELECT id FROM public.documents
            WHERE project_id IN (
                SELECT id FROM public.projects WHERE owner_id = auth.uid()
            )
        )
    );

-- =============================================================================
-- 7. CHANGE REQUESTS TABLE
-- =============================================================================
CREATE TABLE public.change_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    document_id UUID REFERENCES public.documents(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    impact_analysis TEXT,
    requested_by UUID REFERENCES auth.users(id),
    status VARCHAR(50) DEFAULT 'pending'::varchar, -- 'pending', 'approved', 'rejected', 'implemented'
    approved_by UUID REFERENCES auth.users(id),
    approved_at TIMESTAMPTZ,
    jira_cr_key VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS for change_requests
ALTER TABLE public.change_requests ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view change requests of their projects"
    ON public.change_requests FOR SELECT
    USING (
        project_id IN (
            SELECT id FROM public.projects 
            WHERE owner_id = auth.uid() 
            OR auth.uid() IN (SELECT jsonb_array_elements_text(stakeholders::jsonb))::UUID
        )
    );

CREATE POLICY "Users can insert change requests for their projects"
    ON public.change_requests FOR INSERT
    WITH CHECK (
        project_id IN (
            SELECT id FROM public.projects WHERE owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can update change requests for their projects"
    ON public.change_requests FOR UPDATE
    USING (
        project_id IN (
            SELECT id FROM public.projects WHERE owner_id = auth.uid()
        )
    );

-- =============================================================================
-- 8. TEST CASES TABLE
-- =============================================================================
CREATE TABLE public.test_cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_story_id UUID NOT NULL REFERENCES public.user_stories(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    test_steps JSONB DEFAULT '[]'::jsonb,
    expected_result TEXT,
    priority VARCHAR(50) DEFAULT 'medium'::varchar,
    status VARCHAR(50) DEFAULT 'draft'::varchar,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS for test_cases
ALTER TABLE public.test_cases ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view test cases of their projects"
    ON public.test_cases FOR SELECT
    USING (
        user_story_id IN (
            SELECT id FROM public.user_stories
            WHERE feature_id IN (
                SELECT id FROM public.features
                WHERE project_id IN (
                    SELECT id FROM public.projects 
                    WHERE owner_id = auth.uid() 
                    OR auth.uid() IN (SELECT jsonb_array_elements_text(stakeholders::jsonb))::UUID
                )
            )
        )
    );

CREATE POLICY "Users can insert test cases for their projects"
    ON public.test_cases FOR INSERT
    WITH CHECK (
        user_story_id IN (
            SELECT id FROM public.user_stories
            WHERE feature_id IN (
                SELECT id FROM public.features
                WHERE project_id IN (
                    SELECT id FROM public.projects WHERE owner_id = auth.uid()
                )
            )
        )
    );

CREATE POLICY "Users can update test cases for their projects"
    ON public.test_cases FOR UPDATE
    USING (
        user_story_id IN (
            SELECT id FROM public.user_stories
            WHERE feature_id IN (
                SELECT id FROM public.features
                WHERE project_id IN (
                    SELECT id FROM public.projects WHERE owner_id = auth.uid()
                )
            )
        )
    );

-- =============================================================================
-- 9. AGENT SESSIONS TABLE (for tracking AI BA conversations)
-- =============================================================================
CREATE TABLE public.agent_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    current_step INTEGER DEFAULT 1,
    context JSONB DEFAULT '{}'::jsonb,
    elicitation_answers JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(50) DEFAULT 'active'::varchar,
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS for agent_sessions
ALTER TABLE public.agent_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own agent sessions"
    ON public.agent_sessions FOR SELECT
    USING (created_by = auth.uid());

CREATE POLICY "Users can insert agent sessions for their projects"
    ON public.agent_sessions FOR INSERT
    WITH CHECK (created_by = auth.uid());

CREATE POLICY "Users can update their own agent sessions"
    ON public.agent_sessions FOR UPDATE
    USING (created_by = auth.uid());

-- =============================================================================
-- 10. API INTEGRATIONS TABLE (for Jira, Confluence, Gmail configs)
-- =============================================================================
CREATE TABLE public.api_integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    integration_type VARCHAR(50) NOT NULL, -- 'JIRA', 'CONFLUENCE', 'GMAIL'
    config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS for api_integrations
ALTER TABLE public.api_integrations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view integrations of their projects"
    ON public.api_integrations FOR SELECT
    USING (
        project_id IN (
            SELECT id FROM public.projects WHERE owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert integrations for their projects"
    ON public.api_integrations FOR INSERT
    WITH CHECK (
        project_id IN (
            SELECT id FROM public.projects WHERE owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can update integrations for their projects"
    ON public.api_integrations FOR UPDATE
    USING (
        project_id IN (
            SELECT id FROM public.projects WHERE owner_id = auth.uid()
        )
    );

-- =============================================================================
-- FUNCTIONS & TRIGGERS
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON public.projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_milestones_updated_at BEFORE UPDATE ON public.milestones
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_features_updated_at BEFORE UPDATE ON public.features
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_stories_updated_at BEFORE UPDATE ON public.user_stories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON public.documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_change_requests_updated_at BEFORE UPDATE ON public.change_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_test_cases_updated_at BEFORE UPDATE ON public.test_cases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_sessions_updated_at BEFORE UPDATE ON public.agent_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_integrations_updated_at BEFORE UPDATE ON public.api_integrations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to create document version on update
CREATE OR REPLACE FUNCTION create_document_version()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.content IS DISTINCT FROM NEW.content THEN
        INSERT INTO public.document_versions (document_id, version_number, content, change_summary, changed_by)
        VALUES (NEW.id, NEW.current_version, OLD.content, 'Auto-saved version', NEW.created_by);
        NEW.current_version = NEW.current_version + 1;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER document_version_trigger BEFORE UPDATE ON public.documents
    FOR EACH ROW EXECUTE FUNCTION create_document_version();

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================
CREATE INDEX idx_milestones_project_id ON public.milestones(project_id);
CREATE INDEX idx_features_project_id ON public.features(project_id);
CREATE INDEX idx_features_milestone_id ON public.features(milestone_id);
CREATE INDEX idx_user_stories_feature_id ON public.user_stories(feature_id);
CREATE INDEX idx_documents_project_id ON public.documents(project_id);
CREATE INDEX idx_document_versions_document_id ON public.document_versions(document_id);
CREATE INDEX idx_change_requests_project_id ON public.change_requests(project_id);
CREATE INDEX idx_test_cases_user_story_id ON public.test_cases(user_story_id);
CREATE INDEX idx_agent_sessions_project_id ON public.agent_sessions(project_id);
CREATE INDEX idx_api_integrations_project_id ON public.api_integrations(project_id);
