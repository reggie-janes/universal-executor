import pytest

from core.tool_api import export


def test_export_accepts_zero_args():
    @export("ok")
    def ok():
        pass

    assert ok.__tool_description__ == "ok"


def test_export_rejects_required_positional():
    with pytest.raises(TypeError, match="must take no arguments"):
        @export("plus")
        def plus(a, b):
            pass


def test_export_rejects_keyword_only():
    with pytest.raises(TypeError, match="must take no arguments"):
        @export("bad")
        def bad(*, k):
            pass


def test_export_allows_defaults_and_varargs():
    @export("ok")
    def ok(x=0, *args, **kwargs):
        pass

    assert ok.__tool_description__ == "ok"


def test_export_message_names_function_and_first_param():
    with pytest.raises(TypeError) as ei:
        @export("plus")
        def plus(a, b):
            pass

    msg = str(ei.value)
    assert "plus" in msg
    assert "a" in msg and "b" in msg
    assert 'a: input(int, "...") = 0' in msg
