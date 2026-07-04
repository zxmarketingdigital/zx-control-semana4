---
name: graphify
description: any input (code, docs, papers, images) → knowledge graph → clustered communities → HTML + JSON + audit report. Trigger /graphify
trigger: /graphify
model: sonnet
effort: high
---

# /graphify

Turn folder of files (code, docs, papers, images, video) into navigable knowledge graph with community detection, audit trail, and outputs: interactive HTML, GraphRAG JSON, GRAPH_REPORT.md.

## Full reference

Detailed pipeline (9 steps), all flags, subcommands (`add`, `query`, `path`, `explain`, `--update`, `--watch`, `--mcp`, `--neo4j`, `--obsidian`, `--wiki`, etc.), subagent prompts, and honesty rules in **`reference.md`** (same folder).

**Read `reference.md` BEFORE running anything** — the pipeline is multi-step with strict ordering, parallel subagent dispatch rules, and JSON schemas that must be followed exactly. Do not improvise.

## Quick usage

```
/graphify [path]                    # full pipeline
/graphify [path] --mode deep        # richer INFERRED edges
/graphify [path] --update           # re-extract changed files only
/graphify query "<question>"        # BFS traversal
/graphify path A B                  # shortest path
/graphify add <url>                 # ingest URL → ./raw → update
```

Outputs land in `./graphify-out/` (graph.html, graph.json, GRAPH_REPORT.md).
