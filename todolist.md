## ✅ To-Do List

### **Immediate Tasks (Setup & Foundations)**

1. **Environment Setup**

   * Spin up a fresh dev environment (frontend, backend, DB).
   * Clear out old/mockup code.
   * Keep architecture cloud-ready.

2. **Database**

   * Define schema for:

     * Projects → ID, name, category, portfolio, status, active/inactive.
     * Reports → week, raw data, AI analysis, risk/similarity scores, negative keyword flags.
     * Permissions → roles + user assignments (for future SSO).
   * Decide: one **universal table** or separate per category (EPC, Finance, Dev, Investment).

---

### **Development Tasks (Core Features)**

3. **Frontend**

   * Project Management: search, add/edit/remove via pop-ups; toggle active/inactive.
   * Report Screen: upload DOC/Excel, show extracted lines, let users fix AI output.
   * FAQ: predefined questions, but only after user selects a project.
   * UI polish: replace mockups, add filters/search.

4. **Backend**

   * Refactor `main.py` + `analyze_stream.py` for clean prompt handling.
   * Handle CW week + date calculations.
   * Add socket comms for async analysis.
   * Cache AI results in DB → don't re-query ChatGPT unnecessarily.

5. **AI Integration**

   * Better prompts for:

     * Project names/details.
     * Risk/similarity scoring.
     * FAQ that scales to big datasets.
   * Handle missed/duplicate project names gracefully.
   * Highlight negative keywords in reports.

---

### **Medium-Term Tasks (Enhancements & Scaling)**

6. **Advanced Features**

   * Excel import/export.
   * Risk analysis dashboards/visuals.
   * Multi-language UI.
   * Smarter linking of cross-category projects.

7. **Permissions & Security**

   * Add role-based access (admin, PLC, user).
   * Build schema for permissions & assignments.
   * Plan MS 365 Single Sign-On integration.

8. **Performance & Deployment**

   * Speed up batch AI analysis (200+ projects).
   * Improve caching + background processing.
   * Move from local server → cloud once stable.

## DB

### **Phase 1: Core Database Setup (PostgreSQL + FastAPI)**

#### **Step 1: Database Schema Implementation**
1. **Create PostgreSQL Database**
   - Set up PostgreSQL instance (local/cloud)
   - Create database: `qenergy_platform`
   - Enable required extensions: `pgcrypto`, `uuid-ossp`

2. **Implement Core Tables (Priority: Schema Design)**
   - **Projects Table**
     ```sql
     CREATE TABLE projects (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       project_code VARCHAR(32) UNIQUE NOT NULL,
       project_name VARCHAR(255) NOT NULL,
       portfolio_cluster VARCHAR(128),
       status INTEGER NOT NULL CHECK (status IN (0, 1)),
       created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
       created_by VARCHAR(255) NOT NULL,
       updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
       updated_by VARCHAR(255) NOT NULL
     );
     ```
   
   - **Project History Table**
     ```sql
     CREATE TABLE project_history (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       project_code VARCHAR(32) NOT NULL REFERENCES projects(project_code),
       category VARCHAR(128),
       entry_type VARCHAR(50) NOT NULL CHECK (entry_type IN ('Report', 'Issue', 'Decision', 'Maintenance', 'Meeting minutes', 'Mid-update')),
       log_date DATE NOT NULL,
       cw_label VARCHAR(8),
       title VARCHAR(255),
       summary TEXT NOT NULL,
       next_actions TEXT,
       owner VARCHAR(255),
       attachment_url VARCHAR(1024),
       created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
       created_by VARCHAR(255) NOT NULL,
       updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
       updated_by VARCHAR(255) NOT NULL,
       UNIQUE(project_code, log_date)
     );
     ```
   
   - **Weekly Report Analysis Table**
     ```sql
     CREATE TABLE weekly_report_analysis (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       project_code VARCHAR(32) NOT NULL REFERENCES projects(project_code),
       category VARCHAR(128),
       cw_label VARCHAR(8) NOT NULL,
       language VARCHAR(2) NOT NULL DEFAULT 'EN',
       risk_lvl DECIMAL(5,2) CHECK (risk_lvl >= 0 AND risk_lvl <= 100),
       risk_desc VARCHAR(500),
       similarity_lvl DECIMAL(5,2) CHECK (similarity_lvl >= 0 AND similarity_lvl <= 100),
       similarity_desc VARCHAR(500),
       negative_words JSONB,
       created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
       created_by VARCHAR(255) NOT NULL,
       UNIQUE(project_code, cw_label, language)
     );
     ```

3. **Create Indexes for Performance**
   ```sql
   -- Projects table indexes
   CREATE INDEX idx_projects_status ON projects(status);
   CREATE INDEX idx_projects_portfolio ON projects(portfolio_cluster);
   CREATE INDEX idx_projects_created_at ON projects(created_at);
   
   -- Project history indexes
   CREATE INDEX idx_project_history_project_code ON project_history(project_code);
   CREATE INDEX idx_project_history_log_date ON project_history(log_date);
   CREATE INDEX idx_project_history_cw_label ON project_history(cw_label);
   CREATE INDEX idx_project_history_category ON project_history(category);
   
   -- Analysis table indexes
   CREATE INDEX idx_analysis_project_cw ON weekly_report_analysis(project_code, cw_label);
   CREATE INDEX idx_analysis_risk_lvl ON weekly_report_analysis(risk_lvl DESC);
   CREATE INDEX idx_analysis_similarity_lvl ON weekly_report_analysis(similarity_lvl DESC);
   ```

#### **Step 2: FastAPI Backend Setup**
1. **Create FastAPI Project Structure**
   ```
   backend/
   ├── app/
   │   ├── __init__.py
   │   ├── main.py
   │   ├── database.py
   │   ├── models/
   │   │   ├── __init__.py
   │   │   ├── project.py
   │   │   ├── project_history.py
   │   │   └── analysis.py
   │   ├── schemas/
   │   │   ├── __init__.py
   │   │   ├── project.py
   │   │   ├── project_history.py
   │   │   └── analysis.py
   │   ├── api/
   │   │   ├── __init__.py
   │   │   ├── projects.py
   │   │   ├── project_history.py
   │   │   └── analysis.py
   │   └── utils/
   │       ├── __init__.py
   │       ├── cw_calculator.py
   │       └── validators.py
   ├── requirements.txt
   └── alembic/
   ```

2. **Database Connection Setup**
   - Install dependencies: `fastapi`, `sqlalchemy`, `psycopg2-binary`, `alembic`
   - Configure database URL in environment variables
   - Set up SQLAlchemy engine and session management

3. **Basic CRUD Operations**
   - Implement basic GET/POST/PUT/DELETE for each table
   - Add proper error handling and validation
   - Implement pagination for large datasets

#### **Step 3: Core API Endpoints**
1. **Projects API**
   - `GET /api/projects` - List with pagination, search, filtering
   - `POST /api/projects` - Create single project
   - `PUT /api/projects/{project_code}` - Update project
   - `DELETE /api/projects/{project_code}` - Delete project
   - `POST /api/projects/bulk-upload` - Excel/CSV bulk replace

2. **Project History API**
   - `GET /api/project-history` - List with filters (project, date range, category)
   - `POST /api/project-history` - Create history entry
   - `PUT /api/project-history/{id}` - Update history entry
   - `GET /api/project-history/{project_code}/timeline` - Get project timeline

3. **Analysis API**
   - `GET /api/analysis` - List analysis results
   - `POST /api/analysis/run` - Start analysis job
   - `GET /api/analysis/{project_code}/{cw_label}` - Get specific analysis

### **Phase 2: Advanced Features (Future)**

#### **Step 4: Authentication & Authorization**
1. **User Management**
   - Implement JWT-based authentication
   - Add user roles and permissions
   - Audit trail for all operations

#### **Step 5: AI Integration**
1. **OpenAI Integration**
   - Set up OpenAI API client
   - Implement analysis prompts
   - Add result caching and reuse logic

#### **Step 6: WebSocket Support**
1. **Real-time Updates**
   - WebSocket connection for analysis progress
   - Real-time notifications

### **Implementation Notes**

**Priority Conflicts Resolved:**
- Schema design takes priority over project design
- `project_code` is used as business identifier (not `id`)
- `status` is INTEGER (0/1) not boolean
- All timestamps are UTC with timezone
- Audit fields (`created_by`, `updated_by`) are required
- CW calculation follows Monday-start rule

**Key Differences from Project Design:**
- Simplified initial implementation (no complex UI features initially)
- Focus on core data operations first
- Authentication can be added later
- WebSocket features deferred to Phase 2

**Testing Strategy:**
1. **Database Testing**
   - Unit tests for each table
   - Constraint validation tests
   - Performance tests with large datasets

2. **API Testing**
   - Endpoint functionality tests
   - Error handling tests
   - Integration tests with frontend

**Deployment Considerations:**
- Use environment variables for database connection
- Implement proper logging
- Add health check endpoints
- Consider using Docker for containerization
