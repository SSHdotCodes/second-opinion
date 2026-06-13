# Agent Integration Surfaces

Second Opinion uses each agent's native local skill surface and avoids changing broader settings.

| Agent | Integration | Installed file |
| --- | --- | --- |
| Codex | Agent Skill | `~/.agents/skills/second-opinion/SKILL.md` |
| Claude Code | Skill | `~/.claude/skills/second-opinion/SKILL.md` |
| OpenCode | Agent Skill | `~/.config/opencode/skills/second-opinion/SKILL.md` |
| Grok Build | Skill | `~/.grok/skills/second-opinion/SKILL.md` |

## Runtime Delegation

The skill does not create an always-on server. When a parent agent chooses to delegate, it runs:

```bash
second-opinion ask <target-or-auto> --from <caller> --cwd "$PWD" --mode consult -- "Task text"
```

The CLI wraps the target agent's documented non-interactive mode:

- Codex: `codex exec`
- Claude Code: `claude --bare -p`
- OpenCode: `opencode run`
- Grok Build: `grok -p`

## Modes

`consult` is the default. It tells the target agent to inspect and report without changing files and uses the safest available CLI policy.

`work` is for narrow implementation slices. The parent agent should assign non-overlapping files and verify the subagent's result before integrating it.

## Why Skills Instead Of Config Mutation

Second Opinion intentionally avoids editing:

- Agent model defaults
- Provider credentials
- MCP server lists
- Hooks
- Permission rules
- Project config files

This keeps the install reversible and auditable. `second-opinion uninstall --all` removes only files that contain the Second Opinion managed-file marker.
