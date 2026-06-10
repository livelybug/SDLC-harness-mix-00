# Refactor the file structure in `raw-harness-repo/`


# Files to move

* Move files below to `raw-harness-repo/docs`
```bash
burt@17g:~/p2/src/AI/SDLC-harness-mix/raw-harness-repo$ ls *.md
harness-mix-download.md  idea.md  mul-dir-download-update.md  note.md
burt@17g:~/p2/src/AI/SDLC-harness-mix/raw-harness-repo$ ls utils/git-archive-01.md 
utils/git-archive-01.md
```
* Move files below to `raw-harness-repo/config`
```bash
burt@17g:~/p2/src/AI/SDLC-harness-mix/raw-harness-repo$ ls repo-urls.md 
repo-urls.md
burt@17g:~/p2/src/AI/SDLC-harness-mix/raw-harness-repo$ ls repos-config.json 
repos-config.json
```
* Move files below to `raw-harness-repo/src/utils`
```bash
burt@17g:~/p2/src/AI/SDLC-harness-mix/raw-harness-repo$ ls urls_to_config.py 
urls_to_config.py
burt@17g:~/p2/src/AI/SDLC-harness-mix/raw-harness-repo$ ls utils/git-archive.py 
utils/git-archive.py
```

* Move download function files below to `raw-harness-repo/src`
```bash
burt@17g:~/p2/src/AI/SDLC-harness-mix/raw-harness-repo$ ls d*.py
dir-download.py  download_repos.py
```

* Move files below to `raw-harness-repo/tests`
```bash
burt@17g:~/p2/src/AI/SDLC-harness-mix/raw-harness-repo$ ls test_*
test_download_repos.py  test_urls_to_config.py
burt@17g:~/p2/src/AI/SDLC-harness-mix/raw-harness-repo$ ls utils/test_git_archive.py 
utils/test_git_archive.py
```

## Refactor Requirement
* After the structure change, many file references in document and code need to update. Need to scan for reference in all file under `raw-harness-repo/`
* After refactor, need ensure the download function "raw-harness-repo/download_repos.py" is working. All the utils are working. All tests are working.
* A bit complex. So the workflow is likely to be: 
  - Relocate all files as required first.
  - Refactor reference of utils related files
  - Refactor reference of utils test related files
  - Test utils
  - Refactor reference of download function related files
  - Refactor reference of download function test related files
  - Test download functions