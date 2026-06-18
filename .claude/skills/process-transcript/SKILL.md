---
name: process-transcript
description: Use when the user wants to process a raw  transcript into structured Obsidian-style markdown notes with topic summaries, detailed sub-topic files, and mermaid diagrams. Triggers on transcript processing, meeting notes, recording analysis.
---

# Process Transcript

## Overview
Transforms a raw transcript into an Obsidian-style note vault: one summary `topics.md` file linking to detailed per-topic files via `[[wiki-links]]`. Supports appending new transcripts to an existing vault.

## Workflow

### Step 1: Read the transcript

Read the full transcript file provided as an argument. The transcript format is timestamped like:

```
[1:00] Two people just do it.
[2:00]: 1500 of them are actual files that have line by line data.
```

### Step 2: Check for existing vaults

Search the project for directories containing a `topics.md` file. Use Glob with `**/topics.md`.

**If existing vaults found**: Ask the user whether to append to an existing vault or create a new one. Present the found paths as options.

**If no vaults found**: Proceed to create a new vault.

### Step 3: If appending, read existing context

Read the existing `topics.md` to understand what topics are already covered. Note the existing `##` headings and their content so you can identify genuinely new topics from the new transcript.

### Step 4: Identify topics

Analyze the transcript for distinct topics. Look for:
- Subject matter changes in the conversation
- New tools being discussed
- New questions or problem domains introduced
- New processes or events being discussed

Group related discussion fragments under the same topic even if the conversation revisits a subject multiple times.

**If appending**: Flag topics that overlap with existing ones. For each overlap, you will ask the user in the next step.

### Step 5: Present topics for approval

Show the user the proposed topic list before writing any files. Format as a numbered list with a one-line description of each.

**If appending**: Mark which topics are new vs. which overlap with existing topics. For overlapping topics, ask: "Should I merge new details into the existing detail file, or create a separate topic?"

Wait for user confirmation or adjustments (merge, split, rename, remove topics) before proceeding.

### Step 6: Write detail files

Create one markdown file per approved topic. Use **kebab-case** filenames derived from the topic title (e.g., `file-loading-process.md`).

**Detail file structure**:

```markdown
**Parent**: [[topics]]

# [Topic Title]

## Overview
[Synthesized prose summary - 2-4 sentences capturing the key points]

## [Contextual sections - name these based on the actual content]
[Organized content with bullets, tables, or prose as appropriate]

[Include selective blockquotes from the transcript ONLY when they capture
key decisions, exact requirements, or important statements worth preserving]

> *"Map it once, remembers from there."*

## [Diagram section - only if the topic involves a process, flow, or relationships]

```mermaid
[Choose diagram type based on content:
 - flowchart TD: for processes with decision points
 - sequenceDiagram: for interactions between actors/systems
 - flowchart LR: for simple linear flows
 - Match complexity to the topic - simple topics get simple diagrams,
   complex multi-step processes get subgraphs, decision nodes, and styling]
   mermaid```

## [Key Decisions / Open Questions / Pain Points - where relevant]
[Extracted from discussion - what was decided, what remains open]
```

**If appending and merging**: Read the existing detail file, then add new sections or extend existing sections with the new information. Do not overwrite existing content.

### Step 7: Write or update topics.md

**New vault**: Create `topics.md` in a new folder. Derive the folder name from the overall subject matter of the transcript.

**Appending**: Add new `##` sections to the bottom of the existing `topics.md`.

**Topics file structure**:

```markdown
# [Vault Title - descriptive name for the overall subject]

## [Topic Title]
- [Key takeaway bullet 1]
- [Key takeaway bullet 2]
- [Key takeaway bullet 3 - aim for 2-5 bullets per topic]
- [[topic-filename|Detailed notes: Topic Title]]
```

Rules for the topics file:
- Each topic gets a `##` heading
- 2-5 bullet points summarizing the most important takeaways
- One or more `[[wiki-links]]` as the final bullets, pointing to the detail file
- Dense topics can have multiple links targeting specific sections: `[[topic-filename#section-heading|Description]]`
- The wiki-link bullets should describe what the linked detail covers

## Important guidelines

- **No speaker attribution** in output files - synthesize the discussion without naming speakers
- **No timestamps** in output files
- **Extract substance, ignore artifacts** - filler words, false starts, and crosstalk in the transcript should be cleaned away, not reproduced
- **Selective quoting only** - include direct quotes only when they capture a key decision, an exact stated requirement, or a particularly clear explanation. Most content should be synthesized prose.
- **Diagram complexity should match topic complexity** - a simple topic with a linear flow gets a simple diagram. A complex multi-step process with decision points gets subgraphs, conditional branches, and styling.
- **Every detail file gets a parent backlink** - `**Parent**: [[topics]]` at the top
- **Prefer creating too few topics over too many** - group related discussion under one topic rather than fragmenting into many small files


