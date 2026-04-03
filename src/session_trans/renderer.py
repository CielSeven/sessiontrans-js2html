"""Render a Conversation into HTML using Jinja2."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .parser import Conversation, Message

TEMPLATE_DIR = Path(__file__).parent / "templates"


def _format_ts(ts: str) -> str:
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%H:%M:%S")
    except Exception:
        return ts


def _format_date(ts: str) -> str:
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return ts


def _truncate(text: str, max_len: int = 3000) -> tuple[str, bool]:
    if len(text) <= max_len:
        return text, False
    return text[:max_len], True


def _format_tool_args(msg: Message) -> str:
    args = msg.tool_args
    if isinstance(args, dict):
        if msg.tool_name == "exec_command" and "cmd" in args:
            return args["cmd"]
        return json.dumps(args, indent=2, ensure_ascii=False)
    return str(args)


def render_html(conv: Conversation, source_file: str = "") -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=True,
    )
    env.filters["format_ts"] = _format_ts
    env.filters["format_date"] = _format_date
    env.filters["format_tool_args"] = _format_tool_args
    env.globals["truncate"] = _truncate
    env.globals["isinstance"] = isinstance
    env.globals["json_dumps"] = lambda x, **kw: json.dumps(x, **kw)

    template = env.get_template("transcript.html")

    originator = conv.meta.originator or "Assistant"
    assistant_label = originator
    if conv.meta.model_provider:
        assistant_label += f" ({conv.meta.model_provider})"

    return template.render(
        meta=conv.meta,
        messages=conv.messages,
        assistant_label=assistant_label,
        originator=originator,
        session_date=_format_date(conv.meta.timestamp),
        source_file=os.path.basename(source_file),
    )
