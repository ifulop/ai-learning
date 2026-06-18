# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a personal AI learning workspace with two main components:
1. A Python tool (`Source/main.py`) that downloads YouTube transcripts and generates AI summaries
2. An Obsidian knowledge vault (`Vaults/Knowledge for AI Industry/`) populated via Claude Code custom skills

## Running the YouTube Processor

```bash
cd Source
pip install -r requirements.txt
python main.py
```

Requires `ANTHROPIC_API_KEY` in `.env` at the project root.

The script prompts for a YouTube URL, then outputs a markdown file to `Output/` with transcript + AI summary.

## Custom Claude Code Skills

Two skills live in `.claude/skills/` and are invoked via `/process-transcript` and `/ask-vault`:

- **process-transcript**: Converts a raw timestamped transcript into a structured Obsidian vault under `Vaults/`. Creates `topics.md` as an index and per-topic kebab-case detail files with mermaid diagrams.
- **ask-vault**: Queries the vault by reading `topics.md` first, then selectively loading relevant detail files to synthesize an answer with wiki-link citations.

## Architecture

**Source/main.py pipeline:**
- `extract_video_id()` → `get_metadata()` (yt-dlp) → `get_transcript()` (youtube-transcript-api) → `generate_summary()` (Claude API) → `build_markdown()` → write to `Output/`
- Uses `claude-sonnet-4-20250514` with 300 max_tokens for summaries
- `get_ai_summary()` separately scrapes YouTube's internal JSON for YouTube's own AI summary (if available)

**Vault structure (`Vaults/Knowledge for AI Industry/`):**
- `topics.md`: Index file listing all topics with one-line descriptions
- `<topic-name>.md`: Detail files with backlink to topics.md, no speaker attribution, selective direct quotes only

## Key Constraints

- `.claude/settings.local.json` restricts Claude Code Bash permissions to `ls` only — extend this when running the script or other commands requires broader access
- The vault format enforced by process-transcript: parent backlinks required, kebab-case filenames, mermaid diagrams for complex multi-part topics
