please create a Python file in the current folder `raw-harness-repo`. The Python code will:
* Iterate Each URL(a repository in GitHub) in the file `raw-harness-repo/repo-urls.md`. 
* Download.
  * Check if the folder for every repository already existed 
    * if not: Intial download: Setup and download each repository in single branch mode according to (## Download Rule) below. 
    * if yes: Subsequent update: update each repository according to (## Download Rule) below.

## Config  
* In each repository, there only some folders(not all) containing all the AI agent skills. So there will be a configuration array list containing the skill folders for each repository. but now, skill folders are not decided, so for each repository in the configuration, we will have an empty list.

## Download Rule
* Download only skill folders in the config for each repo.
* Please refer to `raw-harness-repo/dir-download.py` for how to setup&download, update each repo.
  
