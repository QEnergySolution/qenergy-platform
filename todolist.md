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
   * Cache AI results in DB → don’t re-query ChatGPT unnecessarily.

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
