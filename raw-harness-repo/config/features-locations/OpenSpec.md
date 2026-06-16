# https://github.com/Fission-AI/OpenSpec.git

## Skill MD files

There is no single folder of pre-written skill `.md` files to copy directly. The skill content is **generated at runtime** from TypeScript template functions — there are no static `.md` source files in the repo.


The skill content lives in `src/core/templates/workflows/` as TypeScript functions (e.g., `getExploreSkillTemplate()`, `getApplyChangeSkillTemplate()`, etc.).