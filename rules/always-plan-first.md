---
trigger: always_on
description: "Always perform focused research and require explicit plan approval prior to implementing code changes or executing modifications. Optimize Gemini quota usage, track progress iteratively, and prevent runaway failure loops."
---

## Description
Always perform focused research and require explicit plan approval prior to implementing code changes or executing modifications. Optimize Gemini quota usage, track progress iteratively, and prevent runaway failure loops.

## Context
- **Scope:** Workspace-specific / User-global rule
- **Created via workflow:** `create-new-agent-rule`

---

## Guidelines & Constraints

### 1. Research & Quota Optimization Phase
- **MANDATORY:** Before modifying existing files, writing code, or running destructive shell commands, conduct targeted research and document the proposed changes in an implementation plan artifact named:
  `implementation_plan_<YYYYMMDD_HHmm>.md`
  *(Replace `<YYYYMMDD_HHmm>` with the actual current local date and time, e.g., `implementation_plan_20261028_0915.md`).*
- **Quota & Token Efficiency:**
  - **Avoid over-researching:** Target specific files and symbols directly; do not read entire large files when checking specific functions (use line ranges/offsets).
  - Avoid redundant directory listings, broad file dumps, or repetitive tool invocations.
  - Keep internal reasoning focused and avoid generating bloated output.
- **Read-Only Constraint:** During this phase, only read-only operations (e.g., viewing files, targeted greps, listing relevant directories) and creating/updating the plan artifact are permitted. No file edits or system modifications.
- **Plan Mode Write-Block Handling:** If `write_file` is denied by a read-only Plan Mode pre-tool hook when creating or updating a required approval artifact (`implementation_plan_<YYYYMMDD_HHmm>.md`, `learning_proposal.md`), **NEVER** paste the plan inline in chat as a substitute. Instead, immediately call `exit_plan_mode` with a single-step handoff instructing the executor to **ONLY** write that artifact (with `RequestFeedback: true`, `UserFacing: true`) and **STOP** without modifying any workspace/config files or running commands until the user explicitly approves.

### 2. Implementation Plan Requirements
Your `implementation_plan_<YYYYMMDD_HHmm>.md` artifact must include:
1. **Goal Description:** Clear, concise summary of the objective.
2. **Proposed Changes:** Exact list of files to create, modify, or delete, along with detailed change descriptions.
3. **Verification Plan:** Concrete automated and manual verification steps to validate functionality.
4. **Open Questions / Assumptions:** Any ambiguities, alternative options, or risks needing clarification.

### 3. User Approval Gate
- Always set `RequestFeedback: true` in the plan artifact's metadata.
- **CRITICAL:** Do NOT proceed to write code, edit files, or execute state-modifying commands until the user reviews and explicitly approves the plan.

### 4. Progress Tracking During Execution
- Immediately upon plan approval, create a `task.md` artifact listing all component-level execution steps as checkboxes.
- **Active Status Updates:** Update `task.md` in real-time as implementation proceeds:
  - `[ ]` — Pending / Not started
  - `[/]` — Currently in progress
  - `[x]` — Completed and verified
- Never batch-complete all tasks at the end; reflect the true live state after each significant step.

### 5. Error Handling & 3-Loop Circuit Breaker
- **Max 3 Retries:** If a command, test, or code change fails, you are permitted at most **5 attempts** to debug and resolve the issue independently.
- **Do NOT loop indefinitely:** If unresolved after 5 attempts, immediately halt execution.
- **Escalate to User:** Document what was attempted, provide the exact error logs, state your hypotheses, and ask the user for guidance or clarification before attempting further fixes.