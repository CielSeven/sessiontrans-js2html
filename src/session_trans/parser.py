"""Parse JSONL session files into a structured conversation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .masker import apply_masks


@dataclass
class Message:
    role: str  # user, assistant, thinking, tool_call, tool_result
    content: str = ""
    timestamp: str = ""
    # tool-specific
    tool_name: str = ""
    tool_args: dict | str = field(default_factory=dict)
    call_id: str = ""


@dataclass
class SessionMeta:
    id: str = ""
    timestamp: str = ""
    model_provider: str = ""
    originator: str = ""
    cli_version: str = ""
    branch: str = ""


@dataclass
class Conversation:
    meta: SessionMeta = field(default_factory=SessionMeta)
    messages: list[Message] = field(default_factory=list)

    def apply_masks(self, rules: list) -> None:
        """Apply masking rules (list of MaskRule) to all text fields."""
        for msg in self.messages:
            msg.content = apply_masks(msg.content, rules)
            msg.tool_name = apply_masks(msg.tool_name, rules)
            if isinstance(msg.tool_args, str):
                msg.tool_args = apply_masks(msg.tool_args, rules)
            elif isinstance(msg.tool_args, dict):
                msg.tool_args = _mask_dict(msg.tool_args, rules)


def _mask_dict(d: dict, rules: list) -> dict:
    out = {}
    for k, v in d.items():
        if isinstance(v, str):
            out[k] = apply_masks(v, rules)
        elif isinstance(v, dict):
            out[k] = _mask_dict(v, rules)
        elif isinstance(v, list):
            out[k] = [apply_masks(i, rules) if isinstance(i, str) else i for i in v]
        else:
            out[k] = v
    return out


_SKIP_PREFIXES = (
    "<permissions",
    "<app-context>",
    "<collaboration_mode>",
    "<skills_instructions>",
    "# AGENTS.md",
    "<environment_context>",
)


def _is_system_text(text: str) -> bool:
    stripped = text.strip()
    return any(stripped.startswith(p) for p in _SKIP_PREFIXES)


def parse_jsonl(path: str | Path) -> Conversation:
    items: list[dict] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))

    conv = Conversation()

    for item in items:
        t = item.get("type")
        payload = item.get("payload", {})
        ts = item.get("timestamp", "")

        if t == "session_meta":
            conv.meta = SessionMeta(
                id=payload.get("id", ""),
                timestamp=payload.get("timestamp", ""),
                model_provider=payload.get("model_provider", ""),
                originator=payload.get("originator", ""),
                cli_version=payload.get("cli_version", ""),
                branch=payload.get("git", {}).get("branch", ""),
            )
            continue

        if t != "response_item":
            continue

        role = payload.get("role")
        ptype = payload.get("type")

        if role == "user" and ptype == "message":
            texts = []
            for c in payload.get("content", []):
                if c.get("type") in ("input_text", "output_text"):
                    text = c.get("text", "")
                    if not _is_system_text(text):
                        texts.append(text)
            if texts:
                conv.messages.append(Message(
                    role="user", content="\n".join(texts), timestamp=ts,
                ))

        elif role == "developer":
            continue

        elif role == "assistant" and ptype == "message":
            texts = []
            for c in payload.get("content", []):
                if c.get("type") == "output_text":
                    texts.append(c.get("text", ""))
            if texts:
                conv.messages.append(Message(
                    role="assistant", content="\n".join(texts), timestamp=ts,
                ))

        elif ptype == "reasoning":
            summary = payload.get("summary", [])
            if summary:
                text = "\n".join(s.get("text", "") for s in summary if s.get("text"))
                if text.strip():
                    conv.messages.append(Message(
                        role="thinking", content=text, timestamp=ts,
                    ))

        elif ptype == "function_call":
            name = payload.get("name", "unknown")
            args_str = payload.get("arguments", "")
            try:
                args = json.loads(args_str) if args_str else {}
            except (json.JSONDecodeError, TypeError):
                args = args_str
            conv.messages.append(Message(
                role="tool_call", tool_name=name, tool_args=args,
                call_id=payload.get("call_id", ""), timestamp=ts,
            ))

        elif ptype == "function_call_output":
            conv.messages.append(Message(
                role="tool_result", content=payload.get("output", ""),
                call_id=payload.get("call_id", ""), timestamp=ts,
            ))

        elif ptype == "custom_tool_call":
            name = payload.get("name", "unknown")
            args = payload.get("input", payload.get("arguments", ""))
            conv.messages.append(Message(
                role="tool_call", tool_name=name, tool_args=args,
                call_id=payload.get("call_id", payload.get("id", "")), timestamp=ts,
            ))

        elif ptype == "custom_tool_call_output":
            conv.messages.append(Message(
                role="tool_result", content=payload.get("output", ""),
                call_id=payload.get("call_id", payload.get("id", "")), timestamp=ts,
            ))

    return conv
