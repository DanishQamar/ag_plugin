---
name: resolve-trivial-conflicts
description: >-
  Use this skill to detect, list, and automatically resolve trivial Git merge
  conflicts where the difference is only whitespace/newlines (PHP) or
  semicolons/whitespace (JavaScript/TypeScript). Resolves hunks by keeping
  current (HEAD) while preserving non-trivial conflicts for review.
---

# Resolve Trivial Conflicts
Author: Danish Qamar <danqam@gmail.com>

Automates the detection and resolution of formatting-only Git merge conflicts across PHP and JS/TS files. When conflicting branches only differ by formatting, tabs, newlines, or semicolons, this workflow lists the occurrences and merges them by keeping the current (`HEAD`) branch content.

## Mandatory Planning Requirement: Clickable Line Numbers
Whenever presenting an implementation plan, conflict breakdown, or dry-run summary to the user:
- **Display the plan directly in the conversation** as a Markdown table.
- **Provide clickable `file://` line number links** for every conflict hunk (e.g., `[<filename>#L<start>-L<end>](file://<abs-path>#L<start>-L<end>)`).
- Show the classification (Trivial vs Non-Trivial), proposed resolution action (Keep Current vs Preserve), and a concise reason/preview so the user can click directly to navigate to each conflict hunk in the editor.

## 1. Pre-Flight & Discovery
1. Ensure the workspace is inside a Git repository with unmerged paths:
   ```bash
   git status --short
   ```
2. Locate the conflict resolution helper script: [resolve-trivial-conflicts.py](./scripts/resolve-trivial-conflicts.py) inside this skill's directory (`<skill-dir>` — e.g., `~/.gemini/config/plugins/gitmerge/skills/resolve-trivial-conflicts` globally or `.agents/plugins/gitmerge/skills/resolve-trivial-conflicts` in a workspace).

## 2. Execution Steps

### Step 1: List & Analyze Conflicts (Dry Run)
Scan unmerged PHP and JS files to inspect trivial vs non-trivial conflict hunks without modifying any files:
```bash
python3 <skill-dir>/scripts/resolve-trivial-conflicts.py --list
```
Add `--verbose` to inspect previews of conflicting current vs incoming code.
Format and display the results in the chat with clickable line number links as required above.

### Step 2: Merge Trivial Conflicts (Keep Current)
Apply automatic resolution by keeping the current (`HEAD`) branch version for all trivial hunks:
```bash
python3 <skill-dir>/scripts/resolve-trivial-conflicts.py --apply
```
- **PHP files (`.php`)**: Hunks are treated as trivial if `re.sub(r'\s+', '', current) == re.sub(r'\s+', '', incoming)`.
- **JS/TS files (`.js`, `.jsx`, `.ts`, `.tsx`, `.vue`)**: Hunks are treated as trivial if `re.sub(r'[\s;]+', '', current) == re.sub(r'[\s;]+', '', incoming)`.
- **Non-trivial hunks**: Left completely untouched with conflict markers preserved for manual inspection.

### Step 3: Review & Stage
- For files where all conflict hunks were trivial, the file is now fully resolved (0 conflict markers remaining).
- Review changes and stage resolved files:
  ```bash
  git diff
  git add <resolved-file>
  ```
  *(Or use `--apply --stage` to automatically stage completely resolved files).*

## 3. Verification Gate
1. Verify no lingering conflict markers (`<<<<<<<`) exist in files reported as fully resolved.
2. Run language syntax checks on resolved files:
   ```bash
   php -l <php-file>
   ```
3. Run `git status` to ensure non-trivial conflict files remain unmerged for review.
