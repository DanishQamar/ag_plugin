# Git Merge Conflict Resolver (`gitmerge`)

Bundles four Git merge conflict resolution skills and their helper scripts into a single Antigravity plugin:

- **`resolve-conflicts`** (`skills/resolve-conflicts/SKILL.md` + `scripts/resolve-conflicts.py`) — Unified two-phase resolver for trivial formatting and non-trivial semantic conflicts.
- **`resolve-trivial-conflicts`** (`skills/resolve-trivial-conflicts/SKILL.md` + `scripts/resolve-trivial-conflicts.py`) — Auto-merges whitespace/newline (PHP) and semicolon/whitespace (JS/TS) conflicts by keeping `HEAD`.
- **`resolve-nontrivial-conflicts`** (`skills/resolve-nontrivial-conflicts/SKILL.md` + `scripts/inspect-conflict.py`) — Extracts hunk diffs, commit intent, and archetypes with clickable line-number choices.
- **`open-unmerged-files`** (`skills/open-unmerged-files/SKILL.md` + `scripts/open-unmerged.sh`) — Detects unmerged Git paths and opens each file in the active IDE positioned at the first conflict marker.

---

## Export the Plugin

Create a portable `.tar.gz` archive (or zip) from `~/.gemini/config/plugins/`:

```bash
tar -czf gitmerge-plugin.tar.gz -C ~/.gemini/config/plugins gitmerge
```

*(Or push the `gitmerge/` folder to a Git repository so teammates/servers can clone or pull updates.)*

---

## Import on a Different Server (Global User Scope)

Copy `gitmerge-plugin.tar.gz` to the target server (`scp gitmerge-plugin.tar.gz user@server:~/`) and extract it into Antigravity's global plugins root:

```bash
mkdir -p ~/.gemini/config/plugins
tar -xzf gitmerge-plugin.tar.gz -C ~/.gemini/config/plugins
```

Verify the manifest exists at `~/.gemini/config/plugins/gitmerge/plugin.json`. Antigravity discovers plugins automatically and loads all four skills on the next turn.

---

## Import into a Project Workspace (Team / Repo Scope)

### Option A: Standard Workspace Discovery (`.agents/plugins/`)
Extract or copy `gitmerge/` directly into `<project-root>/.agents/plugins/`:

```bash
mkdir -p /path/to/project/.agents/plugins
tar -xzf gitmerge-plugin.tar.gz -C /path/to/project/.agents/plugins
```

Commit `<project-root>/.agents/plugins/gitmerge/` to Git so anyone opening the project receives the plugin automatically.

### Option B: Register a Custom Shared Path (`.agents/plugins.json`)
If you store plugins elsewhere (e.g., `tools/agents/plugins/gitmerge/`), register the parent folder in `<project-root>/.agents/plugins.json`:

```json
{
  "entries": [
    {
      "path": "tools/agents/plugins",
      "include_only": ["gitmerge"]
    }
  ]
}
```
