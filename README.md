# flowdiff

An agent skill that reviews a git diff or pull request as diagrams: flowcharts for control flow inside a component, sequence diagrams for how components collaborate. Each changed function is marked added, modified or removed, and clicking it shows the real hunk and reviewer notes. Risks are numbered, marked on the diagram where they happen, and listed with severity and a suggested fix.

Needs Python 3 (standard library only). The generated page loads Mermaid from a CDN.

## Install

Clone this repo into your agent's skills directory, keeping the folder name `flowdiff`:

    git clone https://github.com/rohankmr414/flowdiff ~/.claude/skills/flowdiff

Skills directories by agent:

| Agent | Per user | Per project |
|---|---|---|
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| Codex | `~/.codex/skills/` | `.agents/skills/` |
| OpenCode | `~/.config/opencode/skills/` | `.opencode/skills/` |

Any other agent that reads the SKILL.md format works the same way. An agent without skill support can be told: "read flowdiff/SKILL.md and follow it".

## Use

Ask the agent to review a PR, branch or patch, for example "review PR 123 and show me how the flow changes".

## Try it without an agent

    python3 scripts/render.py references/example.json -o review.html --md review.md

## Layout

- `SKILL.md`: the instructions the agent follows
- `scripts/render.py`: turns `flows.json` into `review.html` and Mermaid markdown
- `assets/template.html`: the review page
- `references/`: two worked examples, one flowchart review and one sequence review
- `evals/`: test cases for the skill

## License

MIT
