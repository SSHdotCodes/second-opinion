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

`consult` is the default. It tells the target agent to inspect and report without changing files and uses the safest available CLI policy.

`work` is for narrow implementation slices. The parent agent should assign non-overlapping files and verify the subagent's result before integrating it.

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
