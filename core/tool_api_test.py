import pytest

from core.tool_api import LabeledEnum, export


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


def test_labeled_enum_falls_back_to_member_name():
    class Unit(LabeledEnum):
        CELSIUS = "C"
        FAHRENHEIT = "F"

    assert Unit.CELSIUS.label == "CELSIUS"
    assert Unit.FAHRENHEIT.label == "FAHRENHEIT"


def test_labeled_enum_call_registers_label_and_returns_member():
    class Unit(LabeledEnum):
        CELSIUS = "C"

    result = Unit.CELSIUS("Celsius degrees")
    assert result is Unit.CELSIUS
    assert Unit.CELSIUS.label == "Celsius degrees"


def test_labeled_enum_call_overrides_previous_label():
    class Unit(LabeledEnum):
        CELSIUS = "C"

    Unit.CELSIUS("first")
    Unit.CELSIUS("second")
    assert Unit.CELSIUS.label == "second"


def test_labeled_enum_subclasses_have_isolated_labels():
    class A(LabeledEnum):
        X = 1

    class B(LabeledEnum):
        X = 1

    A.X("alpha")
    assert A.X.label == "alpha"
    assert B.X.label == "X"  # B inherits no label from A

    B.X("beta")
    assert A.X.label == "alpha"  # A is unaffected by writes to B


def test_labeled_enum_base_class_holds_no_labels_dict():
    # Sanity: defining a subclass and calling its members must not
    # mutate LabeledEnum itself, which would leak across all subclasses.
    class Unit(LabeledEnum):
        CELSIUS = "C"

    Unit.CELSIUS("Celsius degrees")
    assert "_labels" not in LabeledEnum.__dict__
