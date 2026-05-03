# Universal Executor

Auto-generated DearPyGui frontend for plain-Python "tool" modules.

You drop a `.py` file into `tools/` that declares some inputs, some outputs, and a few `@export`-decorated functions. The app discovers it, builds a UI by reflection, and wires every button to the corresponding function call. No registration, no config files, no UI code.

## Quick start

### Linux / macOS / Windows (with [uv](https://docs.astral.sh/uv/))

```bash
uv run python main.py
```

### Windows (no terminal)

Double-click one of the launchers in the repo root:

- `run-uv.vbs` — uses `uv` (auto-creates `.venv` and installs deps)
- `run-global.vbs` — uses the system Python; needs `pip install dearpygui` once

Both run silently with no console window.

## Writing a tool

Drop a file into `tools/`. Click **Reload** in the UI (or restart) to pick it up.

```python
# tools/adder.py
from core.tool_api import input, output, export

tool_name = "Adder"            # optional; falls back to file stem

a: input(int, "first")  = 0    # public input
b: input(int, "second") = 0    # public input
s: output("sum")               # public output (always str)

HIDDEN = 42                    # not in UI — no input()/output() annotation

@export("add")
def add():
    global s
    s = str(a + b)
```

Rules:

- Public I/O is declared as **type annotations** whose value is `input(...)` / `output(...)`. They are not real types — the scanner reads `module.__annotations__`.
- The UI surface of a tool file is exactly: variables annotated with `input()` / `output()`, plus functions decorated with `@export`.
- File naming inside `tools/`: the scanner **skips** any file matching `_*.py` (treat as a private/helper module) or `*_test.py` (pytest files). Use either prefix for files that live in `tools/` but are not themselves tools.
- Outputs are always strings. Use them for both successful results and **soft errors** like `"undefined, can't divide by 0"` — see `tools/demo_calculator.py`. The error popup is reserved for uncaught exceptions.
- (!!!) Exported functions read inputs as module globals and must use `global` to write outputs.

### Supported input types

| "Types"                       | Widget                |
| ----------------------------- | --------------------- |
| `int`                         | numeric input         |
| `float`                       | numeric input         |
| `bool`                        | checkbox              |
| `Enum` subclass               | combo box (member names) |
| `list` / `tuple` of choices   | combo box             |

See `tools/demo_temperature.py` for an `Enum` example.

## Tests

```bash
uv run pytest

# single test
uv run pytest tools/demo_calculator_test.py::test_plus
```

Pytest is configured to look in `tools/` for files matching `*_test.py`. `tools/__init__.py` makes pytest's default `prepend` import mode add the repo root to `sys.path`, so tests can `import tools.<name>` and `from core.tool_api import …`.

## Project layout

```
main.py                 # entry point — sets up viewport, theme, scans tools, builds UI
core/tool_api.py        # author-facing DSL: input(), output(), @export
core/scanner.py         # discovers tools/*.py and builds ToolSpec via reflection
core/settings.py        # JSON-backed user-preferences store
ui/layout.py            # builds the dynamic window for the selected tool
ui/widgets.py           # input/output widget construction + push/pull of values
ui/runner.py            # invokes an @export function; shows uncaught errors in a modal
ui/state.py             # shared tags, dimensions, and DPG helpers (breaks the ui import cycle)
ui/theme.py             # dark "tailwind-ish" theme + Roboto font loading
tools/                  # drop-in tool modules
assets/                 # app icon + Roboto fonts
```

## Dev container note (Linux side of a shared Windows folder)

The repo is designed to be opened both from Windows and from WSL2 / a dev container against the same folder. The two sides keep their virtualenvs separate:

- Windows → default `.venv/`
- Linux   → `.venv-linux/` (set via `UV_PROJECT_ENVIRONMENT=.venv-linux` in `.devcontainer/post-start.sh`)

A non-interactive shell does not source `~/.bashrc`, so when scripting `uv` from one, prefix the env var: `UV_PROJECT_ENVIRONMENT=.venv-linux uv run pytest`.
