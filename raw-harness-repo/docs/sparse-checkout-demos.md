## 2 demos how to download specific dirs in a git repo

### Demo 1
```bash
git clone --no-checkout https://github.com/garrytan/gstack.git --depth 1 --single-branch
cd gstack
git config core.sparseCheckout true
echo '/docs/' > .git/info/sparse-checkout
echo '/agents/' >> .git/info/sparse-checkout
git sparse-checkout reapply
git pull
git checkout
```
### Demo 2
```bash
git init
git remote add origin https://github.com/garrytan/gstack.git
git config core.sparseCheckout true
echo '/docs/' > .git/info/sparse-checkout
echo '/agents/' >> .git/info/sparse-checkout
git sparse-checkout reapply
default_branch=$(git ls-remote --symref origin HEAD | awk '/^ref:/ {print $2}' | sed 's/refs\/heads\///')
echo "Default branch: $default_branch"
git fetch --depth 1 origin $default_branch
git checkout $default_branch
```

## List path in repo
### List pathes of folders containing "SKILL.md"
```
REPO_URL="https://github.com/garrytan/gstack.git"

# 1. Clone the repository tree WITHOUT downloading file contents or checking them out
git clone --filter=blob:none --no-checkout "$REPO_URL" target-repo
cd target-repo

# 2. Find all directories containing "SKILL.md" by searching the remote tree
git ls-tree -r origin/HEAD --name-only | grep '/SKILL\.md$' | while read -r file; do echo "/$(dirname "$file")"; done | sort -u > .git/sparse-dirs.txt

exit
```

### List pathes of all "SKILL.md"
```
REPO_URL="https://github.com/garrytan/gstack.git"

# 1. Clone the repository tree WITHOUT downloading file contents or checking them out
git clone --filter=blob:none --no-checkout "$REPO_URL" target-repo
cd target-repo

# 2. Find all directories containing "SKILL.md" by searching the remote tree
git ls-tree -r origin/HEAD --name-only | grep '/SKILL\.md$' | while read -r file; do echo "/$(dirname "$file")"; done | sort -u > .git/sparse-dirs.txt

exit
```