"""Discover and introspect tool modules in a folder."""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, field
from enum import EnumMeta
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

from .tool_api import Input, Output

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"


@dataclass
class VarSpec:
    name: str
    kind: Any
    description: str
    tooltip: str = ""


@dataclass
class FuncSpec:
    name: str
    description: str
    callable: Callable[[], None]
    tooltip: str = ""


@dataclass
class ToolSpec:
    name: str
    module: ModuleType
    inputs: list[VarSpec] = field(default_factory=list)
    outputs: list[VarSpec] = field(default_factory=list)
    funcs: list[FuncSpec] = field(default_factory=list)


def rescan() -> list[ToolSpec]:
    return discover_tools(TOOLS_DIR)


def discover_tools(tools_dir: Path) -> list[ToolSpec]:
    specs: list[ToolSpec] = []
    for path in sorted(tools_dir.glob("*.py")):
        if not _is_tool_file(path):
            continue
        try:
            module = _load_module(path)
        except Exception as exc:  # noqa: BLE001 — surface load errors at startup
            print(f"[scanner] failed to load {path.name}: {exc}", file=sys.stderr)
            continue
        specs.append(_build_spec(module, fallback_name=path.stem))
    specs.sort(key=lambda s: s.name.lower())
    return specs


def _is_tool_file(path: Path) -> bool:
    if path.suffix != ".py":
        return False
    name = path.stem
    if name.startswith("_"):
        return False
    if name.endswith("_test"):
        return False
    return True


def _load_module(path: Path) -> ModuleType:
    mod_name = f"_uex_tool_{path.stem}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot create spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


def _build_spec(module: ModuleType, fallback_name: str) -> ToolSpec:
    name = getattr(module, "tool_name", fallback_name)
    spec = ToolSpec(name=str(name), module=module)
    annotations = getattr(module, "__annotations__", {}) or {}
    for var_name, ann in annotations.items():
        if isinstance(ann, Input):
            spec.inputs.append(VarSpec(var_name, ann.kind, ann.description, ann.tooltip))
        elif isinstance(ann, Output):
            if not hasattr(module, var_name):
                setattr(module, var_name, "")
            spec.outputs.append(VarSpec(var_name, str, ann.description, ann.tooltip))
    for attr_name, attr in vars(module).items():
        if attr_name.startswith("_"):
            continue
        desc = getattr(attr, "__tool_description__", None)
        if callable(attr) and desc is not None:
            tooltip = getattr(attr, "__tool_tooltip__", "") or ""
            spec.funcs.append(FuncSpec(attr_name, desc, attr, tooltip))
    return spec


def is_enum_kind(kind: Any) -> bool:
    return isinstance(kind, EnumMeta)


def is_choices_kind(kind: Any) -> bool:
    return isinstance(kind, (list, tuple))
