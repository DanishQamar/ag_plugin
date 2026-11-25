---
name: open-unmerged-files
description: >-
  Use this skill when the user asks to open unmerged files, git merge conflict
  files, or conflicted paths in the IDE / editor.
---

# Open Unmerged Files in IDE

Opens all files currently in Git's `Unmerged paths` in the user's IDE positioned at the first conflict marker and summarizes the conflict count for each file.

## Steps

1. **Run the bundled helper script:**
   Locate [open-unmerged.sh](./scripts/open-unmerged.sh) inside this skill's directory (`<skill-dir>` — e.g., `~/.gemini/config/plugins/gitmerge/skills/open-unmerged-files` globally or `.agents/plugins/gitmerge/skills/open-unmerged-files` in a workspace):
   ```bash
   bash <skill-dir>/scripts/open-unmerged.sh
   ```
   - Use `--dry-run` (or `--list`) to list unmerged files, conflict counts, and first conflict line numbers without launching the editor.
   - Use `-e <editor>` to override the auto-detected IDE CLI (`agy-ide`, `antigravity-ide`, `code`).

2. **Fallback (if running without the helper script):**
   List unmerged files in the current repository:
   ```bash
   git diff --name-only --diff-filter=U
   ```
   If the output is empty, inform the user that there are no unmerged files in the current repository and stop.

   Otherwise detect the available IDE CLI (`agy-ide`, `antigravity-ide`, `code`, or `agy`), open the files, and count conflict markers:
   ```bash
   IDE_BIN=$(command -v agy-ide || command -v antigravity-ide || command -v code || command -v agy)
   if [ -n "$IDE_BIN" ]; then
       git diff --name-only --diff-filter=U | xargs -r "$IDE_BIN"
   else
       echo "No IDE CLI (agy-ide, antigravity-ide, code, agy) found in PATH."
   fi
   git diff --name-only --diff-filter=U | xargs -r grep -c "^<<<<<<< " || true
   ```

3. **Report to the user:**
   Present a concise markdown table listing each opened file with a clickable `file://` link and its conflict count.
