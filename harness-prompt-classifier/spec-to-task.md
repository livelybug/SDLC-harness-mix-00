# Skills That Break an Implementation Spec / Design / Solution into Actionable Tasks

I searched the vendored skill collection (`harness-repo-skill-collection`) and found multiple skills/prompts that turn a spec, design, or solution into actionable tasks. Below are the most directly relevant ones, organized by where they fit in the spec → tasks pipeline.

## Tier 1 — Direct "Spec/Plan → Actionable Tasks" Skills

These are the canonical matches. Their `description` frontmatter or body explicitly says "break a spec/design into implementable tasks."

| Skill | Path | What it does |
|---|---|---|
| **planning-and-task-breakdown** | `addyosmani/agent-skills/skills/planning-and-task-breakdown/SKILL.md` | The clearest match. Description: *"Breaks work into ordered tasks. Use when you have a spec or clear requirements and need to break work into implementable tasks."* Defines dependency graphs, vertical slicing, XS–XL task sizing, acceptance criteria, checkpoints, and a full plan document template. |
| **writing-plans** | `obra/superpowers/skills/writing-plans/SKILL.md` | Description: *"Use when you have a spec or requirements for a multi-step task, before touching code."* Produces a complete, bite-sized TDD task plan (file paths, exact code, verification commands) from a spec — handoff to `subagent-driven-development` or `executing-plans`. |
| **to-issues** | `mattpocock/skills/skills/engineering/to-issues/SKILL.md` | Description: *"Break a plan, spec, or PRD into independently-grabbable issues on the project issue tracker using tracer-bullet vertical slices."* Outputs numbered vertical-slice issues with Blocked-by chains to an issue tracker. |
| **blueprint** | `affaan-m/ECC/skills/blueprint/SKILL.md` | Description: *"Turn a one-line objective into a step-by-step construction plan… Each step has a self-contained context brief so a fresh agent can execute it cold."* Generates 3–12 PR-sized steps with dependency graph, parallel-step detection, adversarial review, and rollback strategy. |
| **spec-driven-development** | `addyosmani/agent-skills/skills/spec-driven-development/SKILL.md` | Gated SPECIFY → PLAN → TASKS → IMPLEMENT workflow. Phase 3 ("Tasks") explicitly delegates to `planning-and-task-breakdown`; produces per-task acceptance + verify + files. |
| **trellis-spec-bootstrap** | `mindfold-ai/Trellis/.agents/skills/trellis-spec-bootstrap/SKILL.md` | Decomposes spec work by package/layer and routes task planning through `references/spec-task-planning.md`. |
| **plan-orchestrate** | `affaan-m/ECC/skills/plan-orchestrate/SKILL.md` | Orchestrates a multi-phase plan with task breakdown across agents. |
| **orch-add-feature** | `affaan-m/ECC/skills/orch-add-feature/SKILL.md` | End-to-end orchestration: research → plan → TDD per task → review → commit, delegating to ECC agents. |
| **orch-pipeline** | `affaan-m/ECC/skills/orch-pipeline/SKILL.md` | The shared engine that powers `orch-add-feature`/`orch-fix-defect` etc. |
| **ralphinho-rfc-pipeline** | `affaan-m/ECC/skills/ralphinho-rfc-pipeline/SKILL.md` | RFC → tasks pipeline. |
| **gan-planner** agent | (harness agent) | *"Expands a one-line prompt into a full product specification with features, sprints, evaluation criteria, and design direction."* |
| **planner** agent | (harness agent) | *"Expert planning specialist for complex features and refactoring."* Proactive for planning tasks. |
| **Plan** agent | (harness agent) | Software architect agent for designing implementation plans — step-by-step plans, critical files, architectural trade-offs. |

## Tier 2 — Design-to-Task Companion Skills

These complement the above by producing the design that Tier 1 then breaks into tasks.

| Skill | Path | Role |
|---|---|---|
| **brainstorming** | `obra/superpowers/skills/brainstorming/SKILL.md` | Turns a vague idea into an approved design doc; **terminal state is invoking `writing-plans`**. |
| **spec** | `garrytan/gstack/spec/SKILL.md` | Five-phase process: turn vague intent into a precise, executable spec (filed as a GitHub issue with optional `--execute` to spawn an implementing agent). |
| **autoplan** | `garrytan/gstack/autoplan/SKILL.md` | Auto-runs CEO/Design/Eng/DX reviews on a plan and aggregates `### Implementation Tasks` across all phases. |
| **plan-ceo-review**, **plan-eng-review**, **plan-design-review**, **plan-devex-review** | `garrytan/gstack/` | Each review emits a per-phase `tasks-<phase>-*.jsonl` that `autoplan` aggregates. |
| **first-principles-thinking** | `mindfold-ai/Trellis/.agents/skills/first-principles-thinking/SKILL.md` | Decomposes a problem before solutioning. |
| **trellis-brainstorm** | `mindfold-ai/Trellis/.agents/skills/trellis-brainstorm/SKILL.md` | Brainstorm → spec → task chain in the Trellis harness. |

## Tier 3 — Plan Templates / PRP-Style Skills (Spec → Plan → Implementation)

| Skill | Path | Role |
|---|---|---|
| **prp-plan** | (project skill) | Generates a Product Requirement Prompt from a spec. |
| **prp-prd** | (project skill) | PRD-focused version. |
| **prp-implement** | (project skill) | Executes an implementation plan with validation loops. |
| **prp-commit** | (project skill) | Commits implemented tasks with PRP context. |
| **plan** | (project skill) | Standalone plan generation. |
| **multi-plan** | (project skill) | Multi-domain planning. |
| **feature-dev** | (project skill) | Guided feature development with codebase understanding and architecture focus. |
| **prp-pr** | (project skill) | Pull request creation from plan/implementation. |

## Recommended Pick for "Spec → Actionable Tasks"

If you want the single best match, it depends on your starting artifact:

- **You have a spec, want a task plan in markdown** → **`planning-and-task-breakdown`** (addyosmani) or **`writing-plans`** (obra/superpowers).
- **You have a plan, want GitHub issues** → **`to-issues`** (mattpocock).
- **You have a one-liner, want a multi-PR construction plan** → **`blueprint`** (ECC).
- **You have a vague idea** → `brainstorming` → `writing-plans` (obra superpowers chain).
- **You have a spec, want full review + aggregated tasks** → `spec` (gstack) → `autoplan`.
- **You have a spec, want a per-package task list** → `trellis-spec-bootstrap` + `spec-task-planning.md`.
