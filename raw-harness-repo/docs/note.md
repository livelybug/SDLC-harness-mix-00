# Note

## Opensepc

For the repo, the key thing to understand is that the `.ts` files in `src/core/templates/workflows/` are the **source of truth** of the project's skills — the actual skill instructions are embedded as template (`SkillTemplate`) literal strings inside them. 

The `SkillTemplate` object returned has these fields: `name`, `description`, `instructions`, `license`, `compatibility`, `metadata`.

## gstack

For the repo, the skills are in `docs/skills.md`, as need to remove other files in `docs/` after downloading. 