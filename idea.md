Download several very popular and reputable harness repos from GitHub, then use the knowledge base tool to index those harness repos. Then I can query to grab the skills I need quickly.

# Current harness repo status
* The harness repo are downloaded to `raw-harness-repo/repos`
  
# Knowledge Base Tool
* Understand anything: slow
* Onyx: Overqualified
* Deepwiki: file number exceeds limit
* GitNexus: So far good
* CodeGraph: Only for programming languages
* ima: no linux client, need MacOS
  
## Understand anything
### Command to analyse the harness repo

Use the `/understand` with a folder path as an argument.

**For general docs/files:**

```
/understand path/to/your/docs
```

**For Karpathy-pattern LLM wiki:**

```
/understand-knowledge path/to/your/docs
```

**Which one to use?**

- If your docs folder contains  Karpathy-pattern LLM wiki — a three-layer knowledge base with raw sources, wiki markdown, and a schema file — and produces an interactive knowledge graph dashboard, use `/understand-knowledge`
- If your docs folder contains **mixed file types** (code, configs, docs together), use `/understand`.

### Resume

Next: resume by dispatching the remaining 81 file-analyzer batches, then re-run merge to recover the 43 dangling
  cross-batch import edges. (disable recaps in /config)

# GitNexus

Ref: https://www.iliuqi.com/archives/gitnexus-cookbook

## Install & issue fix

### Solution 2: Patch the Installation Script (If you need full functionality)

**Step 1: Install with `--ignore-scripts`**
This prevents `npm` from immediately failing and rolling back the installation.
```bash
npm install -g gitnexus --ignore-scripts
```

**Step 2: Patch `install-utils.js`**
Open the failing script in your text editor. Based on your error log, run:
```bash
nano $(npm root -g)/gitnexus/node_modules/onnxruntime-node/script/install-utils.js
```
1. Add `const http = require('http');` near the top of the file.
2. Inside the file, locate the `https.get` callbacks (inside the `downloadJson` and `downloadFile` functions). Look for the https.get(url, (res) => { line. You will find it in two places in the file (inside the downloadFile function and inside the downloadJson function).
Change (res) => { to function callback(res) {, and paste the redirect logic right underneath it.
:
```javascript
if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
    const mod = res.headers.location.startsWith('https') ? https : http;
    mod.get(res.headers.location, callback).on('error', reject);
    return;
}
```
*(Save and exit the file)*

**Step 3: Manually run the skipped build scripts**
Because we used `--ignore-scripts` in Step 1, we now have to manually trigger the builds for `onnxruntime-node` and GitNexus's other native dependencies (`LadybugDB` and `tree-sitter`). Run the following commands:

```bash
# 1. Install patched onnxruntime-node binaries
cd $(npm root -g)/gitnexus/node_modules/onnxruntime-node
node script/install.js

# 2. Build LadybugDB core
cd $(npm root -g)/gitnexus/node_modules/@ladybugdb/core
node install.js

# 3. Rebuild Tree-Sitter language parsers
cd $(npm root -g)/gitnexus
npm rebuild tree-sitter-typescript
npm rebuild tree-sitter-javascript

# 4. 同样处理 @huggingface/transformers 下的 onnxruntime-node（如果存在）
cd $(npm root -g)/gitnexus/node_modules/@huggingface/transformers/node_modules/onnxruntime-node
node script/install.js

```
