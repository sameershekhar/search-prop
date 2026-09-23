Create a detailed frontend implementation plan based on `.claude/frontend-spec.md`.

Before creating the plan:
1. Read `.claude/search-plan.md`.
2. Read `.claude/frontend-spec.md`.
3. Inspect the existing backend implementation, especially:
   - API routes
   - response schemas
   - query parameters
   - error responses
   - CORS configuration
4. Inspect the existing project structure and any existing frontend files.

Create `.claude/frontend-implementation-plan.md`.

The plan should contain:
1. Files to create or modify
2. React component implementation order
3. API integration approach
4. State management approach
5. Search form implementation
6. Listing card implementation
7. Pagination implementation
8. Loading, empty, and error states
9. CSS/responsive layout approach
10. Testing and manual verification steps

Keep the implementation simple and aligned with `frontend-spec.md`.
Do not write or modify application code yet.
Do not modify the backend.

At the end, summarize:
- planned files
- important implementation decisions
- any mismatch between the frontend spec and the actual backend API
- any assumptions that need to be resolved before implementation