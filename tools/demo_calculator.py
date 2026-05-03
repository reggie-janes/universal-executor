from core.tool_api import input, output, export
from tools import _shared

tool_name = "Simple calculator"

a: input(int, "var a", tooltip="left operand") = 0
b: input(int, "var b", tooltip="right operand") = 0

result: output("result", tooltip="output of the most recent action")


@export("plus", tooltip="a + b")
def plus():
    global result
    result = str(a + b)


@export("minus", tooltip="a - b")
def minus():
    global result
    result = str(a - b)


@export("multiply", tooltip="a × b")
def multiply():
    global result
    result = str(a * b)


@export("divide", tooltip="a ÷ b (b must be non-zero)")
def divide():
    global result
    if b == 0:
        result = "undefined, can't divide by 0"
        return
    result = str(a / b)


@export("sqrt", tooltip="√a (a must be non-negative)")
def sqrt():
    global result
    result = _shared.sqrt(a)
