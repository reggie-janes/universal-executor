from tool_api import input, output, export

tool_name = "Simple calculator"

a: input(int, "var a") = 0
b: input(int, "var b") = 0

result: output("result")


@export("plus")
def plus():
    global result
    result = str(a + b)


@export("minus")
def minus():
    global result
    result = str(a - b)


@export("multiply")
def multiply():
    global result
    result = str(a * b)


@export("divide")
def divide():
    global result
    if b == 0:
        result = "undefined, can't divide by 0"
        return
    result = str(a / b)
