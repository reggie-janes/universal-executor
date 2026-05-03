import sys
import tempfile
from pathlib import Path

from core.scanner import discover_tools


def _write(td: Path, name: str, body: str) -> None:
    (td / name).write_text(body)


def test_renamed_tool_is_evicted_from_sys_modules():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        _write(td, "alpha.py", (
            "from core.tool_api import output, export\n"
            "y: output('y')\n"
            "@export('go')\n"
            "def go():\n"
            "    global y\n"
            "    y = 'alpha'\n"
        ))
        specs, errors = discover_tools(td)
        assert errors == []
        assert "_uex_tool_alpha" in sys.modules

        # Rename: simulate by removing alpha.py and adding beta.py
        (td / "alpha.py").unlink()
        _write(td, "beta.py", (
            "from core.tool_api import output, export\n"
            "y: output('y')\n"
            "@export('go')\n"
            "def go():\n"
            "    global y\n"
            "    y = 'beta'\n"
        ))
        specs, errors = discover_tools(td)
        assert errors == []
        assert "_uex_tool_alpha" not in sys.modules
        assert "_uex_tool_beta" in sys.modules


def test_unsupported_kind_dict_surfaces_as_load_error():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        _write(td, "bad.py", (
            "from core.tool_api import input\n"
            "x: input(dict, 'x') = {}\n"
        ))
        specs, errors = discover_tools(td)
        assert specs == []
        assert len(errors) == 1
        msg = errors[0].traceback
        assert "Unsupported input kind" in msg
        assert "`x`" in msg
        assert "dict" in msg


def test_str_kind_is_accepted():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        _write(td, "ok.py", (
            "from core.tool_api import input, output, export\n"
            "name: input(str, 'name') = 'world'\n"
            "greeting: output('greeting')\n"
            "@export('greet')\n"
            "def greet():\n"
            "    global greeting\n"
            "    greeting = f'hello, {name}'\n"
        ))
        specs, errors = discover_tools(td)
        assert errors == []
        assert len(specs) == 1
        assert specs[0].inputs[0].kind is str


def test_supported_kinds_all_pass():
    from enum import Enum

    class Color(Enum):
        R = 1
        G = 2

    # validate via the helper directly to avoid spinning up modules per kind
    from core.scanner import _validate_input_kind

    for k in (int, float, bool, str):
        _validate_input_kind(k, "v")
    _validate_input_kind(Color, "c")
    _validate_input_kind(["a", "b"], "c")
    _validate_input_kind(("a", "b"), "c")
