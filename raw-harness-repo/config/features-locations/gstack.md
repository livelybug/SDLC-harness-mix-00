# https://github.com/garrytan/gstack.git

## Skill & Agent MD files

### Where the MD Files Live

Each skill has its own folder at the repo root, and each folder contains a `SKILL.md` file. There is **no single flat folder** — they are distributed across individual directories:

```
review/SKILL.md
qa/SKILL.md
ship/SKILL.md
investigate/SKILL.md
office-hours/SKILL.md
plan-ceo-review/SKILL.md
... (50+ total)
```

#### Important: SKILL.md files are generated

The `SKILL.md` files are **generated outputs** from `.tmpl` template files — you should not edit them directly. The source of truth is the corresponding `SKILL.md.tmpl` in each folder (e.g., `review/SKILL.md.tmpl`).
