---
name: resolve-conflicts
description: >-
  Use this skill to inspect, analyze, and resolve all Git merge conflicts in a
  repository or file. Automatically merges trivial formatting conflicts (PHP
  whitespace/newlines, JS semicolons/spaces by keeping current HEAD) and provides
  systematic decision guidance with clickable line numbers for non-trivial conflicts.
---

# Unified Conflict Resolver
Author: Danish Qamar <danqam@gmail.com>

Unified workflow for Git merge conflicts combining automated formatting resolution with structured semantic decision support for complex code divergences.

## Mandatory Requirement: Clickable Line Numbers & Structured Options
Whenever presenting conflict breakdowns or implementation plans in the conversation:
- **Render a table directly in the conversation** featuring clickable `file://` line number links: `[<filename>#L<start>-L<end>](file://<abs-path>#L<start>-L<end>)`.
- **For trivial hunks**: Clearly label as trivial and state the action (Keep Current `HEAD`).
- **For non-trivial hunks**: Provide Git intent, classify the archetype, and present structured choices (Option A: Keep HEAD, Option B: Accept Incoming, Option C: Combined Merge) with a clear recommendation.

## 1. Discovery & Conflict Scan
Locate the helper script [resolve-conflicts.py](./scripts/resolve-conflicts.py) inside this skill's directory (`<skill-dir>` — e.g., `~/.gemini/config/plugins/gitmerge/skills/resolve-conflicts` globally or `.agents/plugins/gitmerge/skills/resolve-conflicts` in a workspace).

Scan all unmerged files across the repository or inspect a single file:
```bash
python3 <skill-dir>/scripts/resolve-conflicts.py --list
```
Add `-f <filepath>` to target a single file. Add `--inspect` to preview non-trivial conflict diffs alongside branch context.

## 2. Two-Phase Execution Workflow

### Phase 1: Auto-Merge Trivial Conflicts (Keep Current)
Automatically resolve all formatting-only conflict hunks in-place:
```bash
python3 <skill-dir>/scripts/resolve-conflicts.py --apply-trivial
```
- **PHP**: Resolves hunks differing only by spaces, tabs, and newlines.
- **JS/TS**: Resolves hunks differing only by semicolons, spaces, and newlines.
- **Non-trivial hunks**: Left untouched with conflict markers intact for review.
- *(Use `--stage` to automatically run `git add` on files where 100% of hunks are resolved).*

### Phase 2: Resolve Non-Trivial Conflicts
For all remaining non-trivial conflicts:
1. Inspect the hunks with Git context:
   ```bash
   python3 <skill-dir>/scripts/resolve-conflicts.py -f <filepath> --inspect
   ```
2. Classify archetype:
   - **Parallel Additions**: Combine additions from both branches without dropping either.
   - **Mutually Exclusive Logic**: Determine business priority or combine conditions (`condA || condB`).
   - **Signature / Renaming**: Standardize on the modern naming convention.
   - **Comments vs Active Code**: Confirm if deprecation/cleanup is intentional.
3. Apply chosen resolution and remove conflict markers.

## 3. Verification Gate
1. Validate syntax immediately after applying resolutions:
   ```bash
   php -l <php-file>
   ```
2. Confirm zero lingering markers in resolved files:
   ```bash
   git diff --check <filepath>
   ```
