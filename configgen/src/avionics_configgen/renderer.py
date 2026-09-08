"""Render a DeviceConfigModel into Cisco IOS configuration text.

Determinism contract (research brief, section 14): for a fixed generator
version and a fixed resolved model, output is byte-identical across runs
-- UTF-8, LF newlines, no timestamps, exactly one trailing newline. The
planner is responsible for sorting every collection before it reaches
here; this module does not re-sort anything, so a template bug that
depends on ordering would be caught by the determinism test rather than
silently "working" here too.
"""

from __future__ import annotations

from ipaddress import IPv4Network
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .models import DeviceConfigModel

_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"


def _prefix_to_netmask(prefix_length: int) -> str:
    return str(IPv4Network(f"0.0.0.0/{prefix_length}").netmask)


def _build_environment() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        # Must be True: with trim_blocks, the newline right after an
        # {% include %} tag is consumed by the *including* template, so
        # each included template must supply its own trailing newline or
        # its last line glues directly onto whatever literal text follows
        # the include in the parent template (found via a real rendering
        # bug: "hostname X!" instead of "hostname X" + "!" on its own line).
        keep_trailing_newline=True,
    )
    env.filters["prefix_to_netmask"] = _prefix_to_netmask
    return env


def render_device(model: DeviceConfigModel) -> str:
    env = _build_environment()
    template = env.get_template("ios/device.j2")
    rendered = template.render(device=model)

    # Normalize line endings and collapse any run of 3+ blank lines that
    # falls out of feature-template composition into a single blank line,
    # then guarantee exactly one trailing newline -- part of the
    # byte-identical-output contract above.
    lines = rendered.replace("\r\n", "\n").split("\n")
    normalized: list[str] = []
    blank_run = 0
    for line in lines:
        if line.strip() == "":
            blank_run += 1
            if blank_run > 1:
                continue
        else:
            blank_run = 0
        normalized.append(line.rstrip())

    while normalized and normalized[-1] == "":
        normalized.pop()

    return "\n".join(normalized) + "\n"
