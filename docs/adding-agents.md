# Adding Agents

Second Opinion is registry-driven. A new agent should require one source update and corresponding tests.

## Checklist

1. Add an `Agent` entry to `AGENTS` in `bin/second-opinion`.
2. Set the CLI command name and aliases.
3. Set the native user skill path.
4. Add consult and work command construction in `command_for_agent`.
5. Add target-selection hints in `choose_target` only if needed.
6. Add or update tests in `tests/test_cli.py`.
7. Run:

```bash
python3 -m unittest discover -s tests
SECOND_OPINION_HOME="$(mktemp -d)" bin/second-opinion install --all --yes
```

## Integration Rules

- Prefer a native skill directory when the agent supports Agent Skills.
- Do not edit global settings when a skill file is enough.
- Do not require a new daemon or API key.
- Use the target agent's local authentication and CLI.
- Keep `consult` read-only by prompt and by the safest available CLI flags.
- Keep `work` opt-in and scoped.
- Keep routing model agnostic. Add agent capability hints, not hardcoded default model requirements, unless the target CLI itself requires them.

## Skill Content

All installed skills are generated from `render_skill`. That keeps the behavior consistent across agents and ensures new target agents appear in every generated skill after the registry is updated.
