import tools.demo_calculator as t


def test_plus():
    t.a, t.b = 3, 4
    t.plus()
    assert t.z == "7"
    assert t.y == "0"


def test_minus():
    t.a, t.b = 3, 4
    t.minus()
    assert t.z == "-1"
    assert t.y == "14"


def test_some_func():
    t.a, t.b = 3, 4
    t.some_func()
    assert t.z == "0"
    assert t.y == str(3 + (3 * 2) - 10)


def test_divide():
    t.a, t.b = 8, 2
    t.divide()
    assert t.z == "4.0"
    assert t.y == ""


def test_divide_by_zero():
    t.a, t.b = 8, 0
    t.divide()
    assert t.z == "undefined, can't divide by 0"
    assert t.y == ""
