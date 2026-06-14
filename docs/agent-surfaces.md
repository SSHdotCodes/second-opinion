# Agent Integration Surfaces

Second Opinion uses each agent's native local skill surface and avoids changing broader settings.

It is model agnostic: the registry describes agent surfaces, commands, skill paths, and task-routing hints. The selected agent's own CLI and user settings decide which model runs unless the user explicitly passes a `--model` override.

| Agent | Integration | Installed file |
| --- | --- | --- |
| Codex | Agent Skill | `~/.agents/skills/second-opinion/SKILL.md` |
| Claude Code | Skill via FreedomClaude terminal mode | `~/.claude/skills/second-opinion/SKILL.md` |
| OpenCode | Agent Skill | `~/.config/opencode/skills/second-opinion/SKILL.md` |
| Grok Build | Skill | `~/.grok/skills/second-opinion/SKILL.md` |
| Google Antigravity | Agent Skill | `~/.gemini/antigravity/skills/second-opinion/SKILL.md` |

## Runtime Delegation

The skill does not create an always-on server. When a parent agent chooses to delegate, it runs:

```bash
second-opinion ask <target-or-auto> --from <caller> --cwd "$PWD" --mode consult --background -- "Task text"
second-opinion jobs
second-opinion wait JOB_ID
```

`--background` is the default workflow taught to installed agent skills. It returns a job id immediately, writes output under `~/.second-opinion/jobs/`, and lets the parent agent keep working while the subagent runs.

The CLI wraps the target agent's documented non-interactive mode:

- Codex: `codex exec`
- Claude Code: `freedomclaude` driving normal `claude` terminal mode
- OpenCode: `opencode run`
- Grok Build: `grok -p`
- Google Antigravity: `agy --print`

## Routing Tips

- Claude Code is the best first stop for visual UI, frontend polish, responsive layout, copy tone, and product/design judgment. Use the latest/highest Claude model available to the user, often an Opus-class model when available.
- Codex is the best first stop for backend work, APIs, data flow, tests, repo-wide edits, debugging, and most general implementation tasks.
- OpenCode is fast and easy for model-flexible exploration across configured providers, but quality depends heavily on the selected model.
- Antigravity is best when Google/Gemini, Vertex, Firebase, Cloud Run, or Google-style orchestration matters.
- Grok Build is useful for broad exploration or implementation spikes when installed.

## Modes

`work` is the default. It is for narrow implementation slices and may edit files, so the parent agent should assign non-overlapping files and verify the subagent's result before integrating it.

`consult` is available with `--mode consult`. It tells the target agent to inspect and report without changing files and uses the safest available CLI policy.

## Goal Mode

Goal mode is available with `second-opinion ask --goal "..."`, but it is not the default and should not be recommended for routine delegation. For targets with a known native goal command, Second Opinion includes that target's `/goal ...` command in the subagent prompt.

Use it only when the user explicitly asks to use goals, or when the user has clearly requested a long-running delegated goal:

```bash
second-opinion ask auto --from codex --cwd "$PWD" --mode work --background --goal "Finish the migration tests and report blockers." -- "Work toward this goal in the assigned files only."
```

The parent agent still owns goal tracking. It should keep the returned job id, check `second-opinion jobs`, call `second-opinion wait JOB_ID`, verify output and edits, and avoid declaring the overall user task complete while that delegated goal is running or unresolved.

## Updating

Once installed, update the CLI and existing managed skills with:

```bash
second-opinion update
```

Use `second-opinion update --all-skills` to regenerate every supported skill file from the latest published template. Updates also refresh FreedomClaude by default; use `second-opinion update --skip-freedomclaude` only when you intentionally do not want the Claude terminal-mode wrapper installed.

## Why Skills Instead Of Config Mutation

Second Opinion intentionally avoids editing:

- Agent model defaults
- Provider credentials
- MCP server lists
- Hooks
- Permission rules
- Project config files

This keeps the install reversible and auditable. `second-opinion uninstall --all` removes only files that contain the Second Opinion managed-file marker.
