import tools.demo_calculator as t


def test_plus():
    t.a, t.b = 3, 4
    t.plus()
    assert t.result == "7"


def test_minus():
    t.a, t.b = 3, 4
    t.minus()
    assert t.result == "-1"


def test_multiply():
    t.a, t.b = 3, 4
    t.multiply()
    assert t.result == "12"


def test_divide():
    t.a, t.b = 8, 2
    t.divide()
    assert t.result == "4.0"


def test_divide_by_zero():
    t.a, t.b = 8, 0
    t.divide()
    assert t.result == "undefined, can't divide by 0"
