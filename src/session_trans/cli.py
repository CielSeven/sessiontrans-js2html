"""CLI entry point for session-trans."""

from __future__ import annotations

from pathlib import Path

import click

from .masker import MaskRule, load_masks
from .parser import parse_jsonl
from .renderer import render_html


@click.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option("-o", "--output", "output_path", type=click.Path(), default=None,
              help="Output HTML path. Defaults to <input>.html or output/ dir.")
@click.option("-m", "--masks", "masks_path", type=click.Path(exists=True), default=None,
              help="Mask file with 'sensitive -> replacement' rules, one per line.")
def main(input_path: str, output_path: str | None, masks_path: str | None) -> None:
    """Convert LLM session JSONL files into readable HTML transcripts.

    INPUT_PATH can be a single .jsonl file or a directory containing .jsonl files.
    """
    rules = load_masks(masks_path) if masks_path else []
    if rules:
        click.echo(f"Loaded {len(rules)} mask rule(s)")

    inp = Path(input_path)

    if inp.is_file():
        if output_path is None:
            output_path = str(inp.with_suffix(".html"))
        _convert_one(inp, Path(output_path), rules)
    elif inp.is_dir():
        files = sorted(inp.glob("*.jsonl"))
        if not files:
            click.echo(f"No .jsonl files found in {inp}")
            raise SystemExit(1)
        out_dir = Path(output_path) if output_path else Path("output")
        out_dir.mkdir(exist_ok=True)
        for f in files:
            out = out_dir / f.with_suffix(".html").name
            _convert_one(f, out, rules)
        click.echo(f"Done. {len(files)} file(s) converted to {out_dir}/")
    else:
        click.echo(f"Not found: {inp}")
        raise SystemExit(1)


def _convert_one(src: Path, dst: Path, rules: list[MaskRule]) -> None:
    click.echo(f"  {src.name} -> {dst}")
    conv = parse_jsonl(src)
    if rules:
        conv.apply_masks(rules)
    html = render_html(conv, source_file=str(src))
    dst.write_text(html, encoding="utf-8")
