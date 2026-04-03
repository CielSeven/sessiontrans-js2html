# session-trans

Convert LLM session JSONL files into readable, shareable HTML transcripts.

## Prerequisites

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) package manager

## Install & Build

```bash
# Clone the repo
git clone git@github.com:CielSeven/sessiontrans-js2html.git
cd sessiontrans-js2html

# Install dependencies
uv sync

# (Optional) Build a distributable wheel
uv build
# Output in dist/session_trans-*.whl, installable via pip install dist/*.whl
```

## Input Format

Place your session JSONL files in any directory and pass it as the input path. Each file should be a `.jsonl` file with one JSON object per line, following the Codex session export format:

- `session_meta` — session metadata (model, provider, cwd, etc.)
- `response_item` — conversation turns: user messages, assistant messages, reasoning, function calls, and their outputs
- `event_msg` — event markers (token counts, task lifecycle, etc.)

A typical source is the Codex Desktop app, which exports sessions as `rollout-<timestamp>-<uuid>.jsonl`.

## Usage

```bash
# Convert all .jsonl files in a directory -> output/
uv run session-trans sessions-jsonl/

# Convert a single file
uv run session-trans session.jsonl

# Custom output path
uv run session-trans session.jsonl -o transcript.html

# Custom output directory for batch conversion
uv run session-trans sessions-jsonl/ -o html-out/

# With sensitive info masking
uv run session-trans sessions-jsonl/ -m masks.txt
```

## Masking Sensitive Information

Create a masks file to redact sensitive information from the output:

```
# One rule per line: pattern -> replacement
/Users/me/Projects/secret -> workspace
/Users/me -> ~
myusername -> user
```

Longer patterns are applied first automatically, so specific paths won't be partially matched by shorter rules.

## Output

The generated HTML is self-contained (no external CSS/JS dependencies) and can be opened in any browser or sent directly to others. Tool calls and reasoning traces are collapsed by default for readability.

## Limitations

- Currently only tested with **Codex Desktop** session JSONL exports. Other LLM session formats (Claude Code, etc.) may need parser adjustments.
- Markdown in assistant messages is rendered as plain text (no rich formatting).
- Very large tool outputs are truncated to 3000 characters in the HTML.
