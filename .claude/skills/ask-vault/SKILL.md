---
name: ask-vault
description: Use when the user wants to ask questions about an Obsidian vault created by process-transcript, or query meeting notes, workshop notes, or structured topic files. Triggers on /ask-vault, vault questions, "what did we discuss", topic lookup.
---

# Ask Vault

## Overview

Answer questions about an Obsidian vault using progressive discovery. Read only the `Topics.md` index first, then selectively read linked detail files based on relevance. Never load the entire vault upfront.

## Invocation

`/ask-vault <question>`

The question is everything after `/ask-vault`.

## Vault Detection

1. Look for `Topics.md` (case-insensitive) in the current working directory
2. If not found, search immediate subdirectories (one level deep) using Glob
3. If multiple found, list them and ask the user to pick
4. If none found, tell the user: "No Topics.md found. Navigate into a vault directory or a parent of one."

## Progressive Discovery Algorithm

### Step 1 — Index Scan

Read `Topics.md` in full. Parse:
- Each `##` topic heading
- Bullet-point summaries under each heading
- All `[[wiki-links]]` (both `[[file|label]]` and `[[file#section|label]]`)

### Step 2 — Relevance Ranking

Compare the question against each topic's heading and bullet points. Select the top 1-3 most relevant topics. Collect all `[[wiki-links]]` from those topics as candidate files.

If the question can be fully answered from `Topics.md` summaries alone (e.g. "what topics were discussed?", "give me an overview"), skip to Step 5 — do not read any detail files.

### Step 3 — First Deep Dive

Read the candidate detail files. Synthesize an answer from the combined context of `Topics.md` summaries and detail file content.

### Step 4 — Gap Check

Evaluate whether the answer fully addresses the question:
- Are there references to concepts covered in other topics not yet read?
- Does the answer feel partial or incomplete?
- Did a detail file reference another topic that might contain missing context?

If gaps exist, go back to `Topics.md`, identify additional relevant files, read them, and refine the answer. Repeat at most once — do not loop indefinitely.

### Step 5 — Respond

Deliver the answer in this format:

```
[Direct answer — 2-6 sentences synthesizing the response]

[Optional: bullet points or brief list if the topic is process-heavy]

**Sources:**
- [[detail-file-one|Topic Name]]
- [[detail-file-two#section|Specific Section]]
```

## Answer Rules

- **Synthesize, don't copy-paste.** Rewrite vault content into a clear, direct answer.
- **Be concise.** This is a lookup tool, not a report generator.
- **Use wiki-links for citations.** Format them exactly as the vault does (`[[file|label]]` or `[[file#section|label]]`) so they are clickable in Obsidian.
- **Stay within the vault.** If the vault contains no relevant information, say so clearly. Do not speculate or add knowledge from outside the vault.
- **Minimize reads.** The entire point is lazy loading. If Topics.md answers it, stop there. If one detail file answers it, don't read more.
