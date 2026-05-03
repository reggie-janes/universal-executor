# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Run / test

- Run the app: `uv run python main.py` (or double-click `run-uv.vbs` / `run-global.vbs` on Windows).
- Run tests: `uv run pytest`. Single test: `uv run pytest tools/demo_calculator_test.py::test_plus`.
- Pytest is configured in `pyproject.toml` with `testpaths = ["tools"]` and `python_files = ["*_test.py"]`. `tools/__init__.py` makes pytest's default `prepend` import mode walk up to the repo root and add it to `sys.path`, so tests can `import tools.<name>` and `from core.tool_api import …`.

### Dev container quirk (Linux side of a shared Windows folder)

The repo is intended to be opened from both WSL2 (via `.devcontainer/`) and Windows on the same folder. Linux uses `.venv-linux/`, Windows uses the default `.venv/`. `.devcontainer/post-start.sh` exports `UV_PROJECT_ENVIRONMENT=.venv-linux` into `~/.bashrc`.

Bash tool calls run a non-interactive shell that does NOT source `~/.bashrc`, so prefix `uv` invocations explicitly: `UV_PROJECT_ENVIRONMENT=.venv-linux uv run pytest`. Without the prefix, uv silently creates an orphan `.venv/` that has to be cleaned up.

## Architecture

The app is an auto-generated DearPyGui frontend for plain-Python "tool" modules. The author writes a normal `.py` file; the app discovers it, builds the UI by reflection, and wires button clicks to function calls.

### The DSL (`core/tool_api.py`)

Tool authors import `input`, `output`, `export`. Public I/O is declared as **type annotations whose value is an `Input(kind, description)` or `Output(description)` instance** — not as real types:

```python
from core.tool_api import input, output, export

a: input(int, "var a") = 0   # public input, read by exported funcs
y: output("var y")           # public output, written by exported funcs (always str)

@export("function plus")
def plus():
    global y
    y = str(a + b)
```

The UI surface of a tool file is exactly: annotations whose value is an `Input` / `Output` instance, plus callables tagged with `__tool_description__` (i.e. `@export`-decorated). Other names — constants, helper functions, imports — are invisible to the UI regardless of whether they start with `_`.

File-level skips happen in `core/scanner.py::_is_tool_file`: the scanner ignores `_*.py` (treat as private/helper modules — e.g. shared utilities co-located with tools) and `*_test.py` (pytest files). Use either prefix for `.py` files inside `tools/` that should not show up as tools.

Exported functions read inputs as module globals and must use `global` to write outputs.

Inputs: `kind` may be `int | float | bool | str`, an `Enum` subclass, or a `list/tuple` of choices — see `ui/widgets.py::_make_input_widget`. Unknown kinds raise `TypeError` at scan time and surface in the load-error modal.

Outputs: always `str`, defaulting to `""` (the scanner pre-populates the module attribute if the author omitted an assignment). Use the output for both successful results and **soft-error messages** like `"undefined, can't divide by 0"` (see `tools/demo_calculator.py::divide`). The error popup is reserved for uncaught exceptions — i.e. genuine programmer mistakes.

### Discovery (`core/scanner.py`)

`scanner.rescan()` is the entry point used by `main.py`; it just calls `discover_tools(TOOLS_DIR)` (where `TOOLS_DIR = <repo>/tools`). `discover_tools(tools_dir)` walks `tools/*.py`, loads each as a uniquely-named module via `importlib.util.spec_from_file_location` (so two tools can share variable names without colliding), and builds a `ToolSpec` by:

1. Reading `module.__annotations__` and keeping entries whose annotation is an `Input` or `Output` dataclass instance.
2. Walking `vars(module)` for non-underscore callables tagged with `__tool_description__` (set by `@export`).

`tool_name` (module-level string) overrides the file stem as the display name.

### UI (`ui/layout.py`, `ui/theme.py`)

`build_window` creates a single primary DPG window with a tool combo box at the top. `_select_tool` rebuilds the dynamic area (Actions row, then Inputs and Outputs side-by-side) for the chosen tool, recording widget tags in `_state["input_tags"]` and `_state["output_tags"]`.

When a function button is clicked, `_run`:

1. `_push_inputs` — reads each input widget's value and `setattr`s it onto the tool module's globals.
2. Calls the exported function (which mutates module globals).
3. `_pull_outputs` — reads each output global back and `set_value`s the corresponding output widget.

Errors from the tool are caught and shown in a modal; the tool's traceback does not crash the app. The mouse-wheel handler on the tool combo cycles tools when the combo is hovered/focused (wheel-up = previous, wheel-down = next, with wrap-around).

The OS viewport auto-fits the natural size of the current tool's content via `_fit_viewport_to_content`, an item-resize handler bound to `DYNAMIC_AREA`. It measures the screen-relative rects of the topmost (`TOP_BAR`) and bottommost (`DYNAMIC_AREA`) children and mirrors the top inset onto the bottom for symmetric padding. After `_select_tool` the resize is also re-fired two frames later (`dpg.set_frame_callback`) because the layout hasn't settled on the same frame it's built.

`ui/theme.py` loads Roboto from `assets/` and applies a Tailwind-ish dark palette + rounded styles. Constants (`ACCENT`, `BG`, `PANEL`, etc.) are at the top of the file if you need to retune.

### Adding a new tool

Drop a new `.py` into `tools/` following the pattern in `tools/demo_calculator.py` or `tools/demo_temperature.py`. No registration needed — click **Reload** in the UI (or restart) to pick it up. `tools/__init__.py` exists so test files can `import tools.<name>`; the scanner itself loads each tool with a unique name (`_uex_tool_<stem>`) via `importlib`, bypassing the package.
