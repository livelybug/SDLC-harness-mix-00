# https://github.com/obra/superpowers.git

## Agent MD files
The repo provides specialized subagent prompt templates for software engineering workflows. They are **not** in a single dedicated folder — they are distributed across their respective skill subdirectories under `skills/`.

Here is the full list:

| Agent | File | Purpose |
|---|---|---|
| **Implementer** | `skills/subagent-driven-development/implementer-prompt.md` | Implements a single task from a plan, self-reviews, and reports back |
| **Spec Compliance Reviewer** | `skills/subagent-driven-development/spec-reviewer-prompt.md` | Verifies the implementation matches the spec (nothing more, nothing less) |
| **Code Quality Reviewer** | `skills/subagent-driven-development/code-quality-reviewer-prompt.md` | Reviews code quality, architecture, and test coverage after spec review passes |
| **Senior Code Reviewer** | `skills/requesting-code-review/code-reviewer.md` | Full code review against a git diff range — the base template used by the quality reviewer |
| **Spec Document Reviewer** | `skills/brainstorming/spec-document-reviewer-prompt.md` | Reviews a written spec for completeness and consistency before planning |
| **Plan Document Reviewer** | `skills/writing-plans/plan-document-reviewer-prompt.md` | Reviews a written plan for completeness and spec alignment before implementation | [1](#0-0) [2](#0-1) [3](#0-2) [4](#0-3) [5](#0-4) 

**There is no single folder** containing all agent MD files. To reuse them in your project, you would need to copy them individually from their respective skill subdirectories:



Each file contains a ready-to-use prompt template with `{PLACEHOLDER}` variables you fill in at dispatch time. The `code-quality-reviewer-prompt.md` delegates to `code-reviewer.md` as its base template, so those two are coupled. [6](#0-5)

### Citations

**File:** skills/subagent-driven-development/implementer-prompt.md (L1-3)
```markdown
# Implementer Subagent Prompt Template

Use this template when dispatching an implementer subagent.
```

**File:** skills/subagent-driven-development/spec-reviewer-prompt.md (L1-5)
```markdown
# Spec Compliance Reviewer Prompt Template

Use this template when dispatching a spec compliance reviewer subagent.

**Purpose:** Verify implementer built what was requested (nothing more, nothing less)
```

**File:** skills/requesting-code-review/code-reviewer.md (L1-5)
```markdown
# Code Reviewer Prompt Template

Use this template when dispatching a code reviewer subagent.

**Purpose:** Review completed work against requirements and code quality standards before it cascades into more work.
```

**File:** skills/brainstorming/spec-document-reviewer-prompt.md (L1-5)
```markdown
# Spec Document Reviewer Prompt Template

Use this template when dispatching a spec document reviewer subagent.

**Purpose:** Verify the spec is complete, consistent, and ready for implementation planning.
```

**File:** skills/writing-plans/plan-document-reviewer-prompt.md (L1-5)
```markdown
# Plan Document Reviewer Prompt Template

Use this template when dispatching a plan document reviewer subagent.

**Purpose:** Verify the plan is complete, matches the spec, and has proper task decomposition.
```

**File:** skills/subagent-driven-development/code-quality-reviewer-prompt.md (L10-12)
```markdown
Task tool (general-purpose):
  Use template at requesting-code-review/code-reviewer.md

```
