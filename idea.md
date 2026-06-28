Download several very popular and reputable harness repos from GitHub, then use the knowledge base tool to index those harness repos. Then I can query to grab the skills I need quickly.

# Current harness repo status
* The harness repo are downloaded to `raw-harness-repo/repos`
  
# Knowledge Base Tool
* Understand anything
* Onyx
* Deepwiki
* GitNexus
  
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