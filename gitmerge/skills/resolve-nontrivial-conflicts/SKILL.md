---
name: resolve-nontrivial-conflicts
description: >-
  Use this skill to systematically analyze, understand, and decide how to
  resolve non-trivial Git merge conflicts in a file. Discovers commit intent,
  classifies conflict archetypes, presents clickable line options, and merges safely.
---

# Resolve Non-Trivial Conflicts
Author: Danish Qamar <danqam@gmail.com>

Provides a systematic semantic decision framework to analyze and merge complex, non-trivial Git merge conflicts where code logic, method signatures, rules, or data schemas diverge between branches.

## Mandatory Requirement: Clickable Line Numbers & Structured Options
Whenever presenting a conflict analysis or resolution plan in conversation:
- **Render a table directly in the conversation** with clickable `file://` links containing exact line numbers: `[<filename>#L<start>-L<end>](file://<abs-path>#L<start>-L<end>)`.
- **Explain developer intent** for both Current (`HEAD`) and Incoming branches.
- **Provide 3–4 explicit options per hunk**:
  * **Option A**: Keep Current (`HEAD`) + trade-off
  * **Option B**: Accept Incoming (`MERGE_HEAD`) + trade-off
  * **Option C**: Synthesized Merge (combine both additions/behaviors cleanly)
  * **Option D**: Custom Adaptation (when signatures or schemas require refactoring)
- State an explicit **Recommended Choice** with architectural rationale.

## 1. Pre-Flight & Hunk Extraction
1. Inspect the conflicted file using the conflict inspector [inspect-conflict.py](./scripts/inspect-conflict.py) inside this skill's directory (`<skill-dir>` — e.g., `~/.gemini/config/plugins/gitmerge/skills/resolve-nontrivial-conflicts` globally or `.agents/plugins/gitmerge/skills/resolve-nontrivial-conflicts` in a workspace):
   ```bash
   python3 <skill-dir>/scripts/inspect-conflict.py <filepath>
   ```
2. Pull Git stage references to understand base ancestor vs branch additions:
   - Base (`:1:<path>`), Current (`:2:<path>`), Incoming (`:3:<path>`).
   - Check recent commit logs:
     ```bash
     git log -n 3 --oneline HEAD -- <filepath>
     git log -n 3 --oneline MERGE_HEAD -- <filepath>
     ```

## 2. Decision Framework by Archetype

### A. Parallel Additions (Both Added New Features)
- **Pattern**: HEAD added Method/Rule A; Incoming added Method/Rule B.
- **Resolution**: Combine both. Place both additions in the target class or configuration.

### B. Mutually Exclusive Expression / Value Changes
- **Pattern**: Both branches edited the same condition or assignment with opposing logic.
- **Resolution**: Determine if one branch represents an updated business rule or if a combined condition (e.g. `isPortal || isFeatureActive`) is required.

### C. Signature / Property Renaming
- **Pattern**: One branch renamed a variable or relation, while the other branch added references to the old name.
- **Resolution**: Adopt the modern name and update newly added references to match.

### D. Comments vs Active Code
- **Pattern**: One branch commented out code; the other branch modified that code.
- **Resolution**: Verify if the deprecation is intentional across the repository.

## 3. Application & Verification Gate
1. Apply the chosen resolution per hunk in-place and remove conflict markers.
2. Run language syntax validation immediately:
   ```bash
   php -l <php-file>
   ```
3. Verify that zero broken conflict markers remain before staging:
   ```bash
   git diff --check <filepath>
   ```
