Ran check antigravity_guide for plugin export/CLI commands

An Antigravity plugin is just a plain folder containing `plugin.json` and its bundled subdirectories (`skills/`, `rules/`, `agents/`, `mcp_config.json`, `hooks.json`, `assets/`), so there is no special proprietary export format.

### Before Exporting (Quick Checklist)
- Remove any hardcoded secrets from `mcp_config.json` (use `${VAR}` + `variables` instead).
- Ensure scripts/paths inside `SKILL.md` or `plugin.json` are relative, not hardcoded to your local username or machine.

### Ways to Export a Plugin (using `` as an example)

1. **Export as a `.tar.gz` archive (Linux / macOS / WSL / servers)**
   ```bash
   tar -czf -plugin.tar.gz -C ~/.gemini/config/plugins 
   ```
   *(On another machine: `mkdir -p ~/.gemini/config/plugins && tar -xzf -plugin.tar.gz -C ~/.gemini/config/plugins`)*

2. **Export as a `.zip` archive (easy to share across Windows & Linux)**
   ```bash
   (cd ~/.gemini/config/plugins && zip -r ~/-plugin.zip )
   ```

3. **Export via Git (best for teams & updates)**
   Push the plugin directory to its own Git repo:
   ```bash
   cd ~/.gemini/config/plugins/
   git init && git add . && git commit -m "Initial  plugin"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```
   Anyone can then install it globally (`git clone <repo-url> ~/.gemini/config/plugins/`) or inside a project repo (`git clone` or copy into `<project>/.agents/plugins/`).

4. **Direct copy to another server (`scp` / `rsync`)**
   ```bash
   rsync -avz ~/.gemini/config/plugins/ user@remote-server:~/.gemini/config/plugins/
   ```

If you want me to create the `-plugin.tar.gz` or `.zip` file for you right now, just let me know where to save it.
