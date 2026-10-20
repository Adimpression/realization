# Workstation

Read `TASK.md`, `WORKSTATION.toml`, `ATTACHMENTS.json`, `TOOLS.json`, and `SKILLS.json` when present before acting.

Available attachments:
- session: session_root at /workstation/session
- main: workspace at /workstation/mounts/main
- scratch: scratch at /workstation/scratch
- output: output at /workstation/output
- openai: secret_ref at /workstation/secrets/openai
- skill_input: workspace at /workstation/mounts/skill_input
- skill_tmp: scratch at /workstation/mounts/skill_tmp
- skill_output: output at /workstation/mounts/skill_output
- skills: skill_store at /workstation/skills/store.sqlite3
- skills_exports: skill_exports at /workstation/skills/exports
- skills_imports: skill_imports at /workstation/skills/imports

Allowed capabilities:
- ws.fs.read
- ws.process.run
- ws.markdown.create
- ws.markdown.append
- ws.skill.catalog
- ws.skill.import
- ws.skill.export
- ws.skill.invoke
- ws.skill.compose
