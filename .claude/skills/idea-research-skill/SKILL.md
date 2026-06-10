---
name: idea-research-skill
description: Research idea evaluation and iteration assistant covering the six-stage LLM Wiki pipeline — paper discovery (arXiv/Semantic Scholar), ingest to raw/, Claude Code compiles raw/ to a structured wiki/, Obsidian visualization, multi-model debate (Claude/Gemini/Codex CLI), and Perplexity novelty validation. Use when the user wants to register a new idea, compile a paper wiki, run a multi-model debate, or validate an idea's novelty. Triggered by keywords like "idea validate", "paper wiki", "compile raw", "novelty check", "多模型讨论", "idea 验证", or direct invocation.
---

# Idea Research Skill

Six-stage LLM-Wiki pipeline for research idea evaluation.

## Workspace Layout

Everything lives under the repo-root `idea-research/` directory (gitignored):

```
idea-research/
├── ideas/                  one subdir per idea, slug-named
│   └── <idea-slug>/
│       ├── idea.md         statement, hypothesis, evaluation criteria
│       ├── raw/            source papers in markdown (append-only)
│       ├── wiki/           compiled concept/paper notes (Claude output)
│       │   ├── papers/     paper-level summaries
│       │   ├── concepts/   cross-paper syntheses
│       │   └── gaps/       identified open problems
│       ├── debates/        transcripts of multi-model discussions
│       └── validation/     perplexity novelty reports
├── research.md             shared context across sessions (three-model share)
└── tools/                  shell helpers (arxiv download, mineru, etc.)
```

All wiki content is **LLM-compiled active knowledge**, not a vector index. Re-compile when raw/ changes.

## Phases

### Phase 1 — Ingest

```
User: "ingest arXiv 2401.12345" or pastes a URL
Action:
  1. Download PDF → use Bash: curl/arxiv-tool to idea-research/ideas/<slug>/raw/<arxiv-id>.pdf
  2. Convert PDF → Markdown. Try mineru CLI first, marker as fallback:
       mineru -p <pdf> -o <dir>  (or:  marker_single <pdf> <out>)
     If neither installed, tell the user and skip — do not silently fall back to a text dump.
  3. Save as raw/<arxiv-id>.md — preserve LaTeX for equations, HTML for tables.
  4. Append a line to raw/INDEX.md with paper title, arxiv id, date ingested.
Never modify or delete files already in raw/. It is append-only.
```

### Phase 2 — Compile Wiki

```
Trigger: "compile wiki" or after ingest of new papers
Action:
  1. Read all raw/*.md.
  2. For each new paper, write wiki/papers/<slug>.md with: one-paragraph TL;DR,
     key claims, methods, datasets, results, limitations, related-work cross-refs as [[backlinks]].
  3. Detect recurring concepts across papers; write or update wiki/concepts/<concept>.md
     with cross-paper synthesis and [[backlinks]] to the paper notes.
  4. Identify gaps and write wiki/gaps/<gap>.md — contradictions, missing ablations,
     unverified claims. Each gap is a candidate idea seed.
  5. Run lint checks: orphan links, contradictions across concept notes,
     duplicate concept files with slightly different names.

The wiki is active knowledge: Claude writes it, Claude reads it. Do not treat as RAG.
```

### Phase 3 — Obsidian

Pure consumption layer. Obsidian reads wiki/ via graph view + Dataview. Do not write to wiki/ from Obsidian side — Claude owns wiki/.

### Phase 4 — Multi-Model Debate

```
Trigger: "debate <question>" or "讨论 <question>"
Precondition: wiki/ and debates/shared-research.md are up to date.
Action:
  1. Prepare briefing: relevant wiki/papers + wiki/concepts + wiki/gaps + the question.
  2. Invoke external models via Bash (installed CLIs only; if missing, skip that role and note it):
     - gemini CLI     → web-check role: search latest papers, verify facts
     - codex CLI      → adversarial role: find holes, counter-examples, prior art
     - this Claude    → synthesizer role: reconcile, align with wiki, arbitrate
  3. Save transcript to debates/<date>-<slug>.md with each model's output labeled.
  4. Extract disagreements; write them to wiki/gaps/ as new open questions.
Do not fabricate model outputs if a CLI is missing. Report "gemini CLI not installed, skipped."
```

### Phase 5 — Novelty Validation

```
Trigger: "validate novelty of <idea>"
Action:
  1. Load the idea text from ideas/<slug>/idea.md.
  2. Call Perplexity (via WebFetch or curl to pplx-api if key is in env).
  3. Cross-check with Semantic Scholar API for citation neighbourhood.
  4. Write report to validation/<date>-novelty.md: prior-art matches with similarity notes,
     open gaps, verdict (novel / incremental / covered).
Do not declare novelty without at least one external search step. If all external calls fail,
surface that clearly instead of guessing.
```

### Phase 6 — Iterate

```
After validation, update:
  - ideas/<slug>/idea.md with the verdict and next-step experiments
  - wiki/gaps/ with new questions raised
  - research.md with high-level direction change, if any
Trigger the next Phase-1 ingest when new seed papers are identified.
```

## Invocation Patterns

When the user says things like:
- "帮我 ingest 这篇 arXiv" → Phase 1
- "compile wiki" / "编译知识库" → Phase 2
- "让三个模型讨论一下 <question>" → Phase 4
- "validate 这个 idea 的新颖性" → Phase 5
- "开始新的 idea 研究: <topic>" → create ideas/<slug>/, scaffold subdirs, ask user to paste seed papers

If the user gives a bare idea statement with no phase hint, default to Phase 5 (novelty validation) because it has the lowest cost and highest information gain early on.

## External Tool Contract

Skill assumes these may or may not be installed. Detect, degrade gracefully, report honestly.

| Tool            | Purpose            | Detection       |
|-----------------|--------------------|-----------------|
| `mineru`        | PDF → Markdown     | `which mineru`  |
| `marker_single` | PDF → Markdown (alt) | `which marker_single` |
| `gemini`        | Web-check role     | `which gemini`  |
| `codex`         | Adversarial role   | `which codex`   |
| `curl` + PPLX_API_KEY env | novelty search | env var set |

## Output Discipline

- Wiki files: one concept per file, YAML frontmatter with `type`, `tags`, `updated`.
- Backlinks: `[[target]]` or `[[target|display]]`; Obsidian parses both.
- No emoji unless the user added them. No "as an AI…" preambles. Short, dense notes.
- When the user says "update wiki after reading X", do not also rewrite unrelated files.

## What This Skill Does Not Do

- Does not vector-index the wiki. Wiki is LLM-compiled active knowledge.
- Does not auto-run experiments. Experiment execution happens in the user's normal dev flow; the skill only organizes the knowledge around experiments.
- Does not push anything to git. The entire `idea-research/` tree is gitignored.
