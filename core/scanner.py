"""Discover and introspect tool modules in a folder."""
from __future__ import annotations

import importlib
import importlib.util
import sys
import traceback as _tb
from dataclasses import dataclass, field
from enum import EnumMeta
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

from .tool_api import Input, Output

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
_TOOL_MOD_PREFIX = "_uex_tool_"


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


@dataclass
class LoadError:
    path: Path
    traceback: str


_last_errors: list[LoadError] = []


def rescan() -> list[ToolSpec]:
    global _last_errors
    specs, _last_errors = discover_tools(TOOLS_DIR)
    return specs


def last_load_errors() -> list[LoadError]:
    """Errors from the most recent ``rescan()`` / ``discover_tools()`` call."""
    return list(_last_errors)


def discover_tools(tools_dir: Path) -> tuple[list[ToolSpec], list[LoadError]]:
    specs: list[ToolSpec] = []
    errors: list[LoadError] = []
    _evict_stale_tool_modules(tools_dir)
    _reload_tools_dir_modules(tools_dir, errors)
    for path in sorted(tools_dir.glob("*.py")):
        if not _is_tool_file(path):
            continue
        try:
            module = _load_module(path)
            spec = _build_spec(module, fallback_name=path.stem)
        except Exception:
            errors.append(LoadError(path, _tb.format_exc()))
            continue
        specs.append(spec)
    specs.sort(key=lambda s: s.name.lower())
    return specs, errors


def _evict_stale_tool_modules(tools_dir: Path) -> None:
    """Drop ``sys.modules`` entries for tool files that no longer exist.

    Tools are loaded under names like ``_uex_tool_<stem>``. When a tool file
    is renamed or deleted, the old entry would otherwise stick around forever,
    pinning the previous module object (and its globals) in memory.
    """
    current_stems = {p.stem for p in tools_dir.glob("*.py") if _is_tool_file(p)}
    for name in list(sys.modules):
        if not name.startswith(_TOOL_MOD_PREFIX):
            continue
        stem = name[len(_TOOL_MOD_PREFIX):]
        if stem not in current_stems:
            del sys.modules[name]


def _reload_tools_dir_modules(tools_dir: Path, errors: list[LoadError]) -> None:
    """Reload cached modules whose source lives under ``tools_dir``.

    Tool modules are re-executed below via ``_load_module``, but anything they
    import (e.g. a shared ``_helpers.py`` co-located in ``tools/``) stays
    cached in ``sys.modules`` from the first load. Without this pass, editing
    a helper and clicking Reload would not pick up the change.
    """
    tools_dir_resolved = tools_dir.resolve()
    for name, module in list(sys.modules.items()):
        if name.startswith(_TOOL_MOD_PREFIX):
            continue
        file = getattr(module, "__file__", None)
        if not file:
            continue
        try:
            mod_path = Path(file).resolve()
            mod_path.relative_to(tools_dir_resolved)
        except (OSError, ValueError):
            continue
        try:
            importlib.reload(module)
        except Exception:
            errors.append(LoadError(mod_path, _tb.format_exc()))


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
    mod_name = f"{_TOOL_MOD_PREFIX}{path.stem}"
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
            _validate_input_kind(ann.kind, var_name)
            spec.inputs.append(VarSpec(var_name, ann.kind, ann.description, ann.tooltip))
        elif isinstance(ann, Output):
            if not hasattr(module, var_name):
                setattr(module, var_name, "")
            spec.outputs.append(VarSpec(var_name, str, ann.description, ann.tooltip))
    for attr_name, attr in vars(module).items():
        desc = getattr(attr, "__tool_description__", None)
        if callable(attr) and desc is not None:
            tooltip = getattr(attr, "__tool_tooltip__", "") or ""
            spec.funcs.append(FuncSpec(attr_name, desc, attr, tooltip))
    return spec


def is_enum_kind(kind: Any) -> bool:
    return isinstance(kind, EnumMeta)


def is_choices_kind(kind: Any) -> bool:
    return isinstance(kind, (list, tuple))


_SUPPORTED_SCALAR_KINDS = (int, float, bool, str)


def _kind_repr(kind: Any) -> str:
    return getattr(kind, "__name__", None) or repr(kind)


def _validate_input_kind(kind: Any, var_name: str) -> None:
    if kind in _SUPPORTED_SCALAR_KINDS:
        return
    if is_enum_kind(kind) or is_choices_kind(kind):
        return
    raise TypeError(
        f"Unsupported input kind for `{var_name}`: {_kind_repr(kind)}. "
        f"Supported: int, float, bool, str, an Enum subclass, "
        f"or a list/tuple of choices."
    )
