from tool_api import input, output, export

tool_name = "Simple calculator"

_C = 10

def _helper():
    return a * 2

a: input(int, "var a") = 0
b: input(int, "var b") = 0

y: output("var y")
z: output("var z")


@export("function plus")
def plus():
    global y, z
    z = str(a + b)
    y = "0"


@export("function for minus")
def minus():
    global y, z
    z = str(a - b)
    y = str(a * b + 2)


@export("just some function")
def some_func():
    global y, z
    z = "0"
    y = str(a + _helper() - _C)


@export("function divide")
def divide():
    global y, z
    if b == 0:
        z = "undefined, can't divide by 0"
        y = ""
        return
    z = str(a / b)
    y = ""
