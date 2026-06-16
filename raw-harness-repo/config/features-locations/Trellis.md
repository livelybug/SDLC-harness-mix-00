# https://github.com/mindfold-ai/Trellis.git

## Agent MD files

Yes, the repo provides 3 specialized agents. Here's the full picture:

## The 3 Agents

| Agent | File | Role |
|---|---|---|
| `trellis-implement` | `implement.md` | Code implementation — reads specs/PRD, writes code, runs lint/typecheck. No git commits allowed. |
| `trellis-check` | `check.md` | Code quality review — diffs changes against specs, self-fixes issues, runs verification. |
| `trellis-research` | `research.md` | Research expert — finds internal patterns or fetches external SDKs/APIs, populates JSONL context files for downstream agents. |
