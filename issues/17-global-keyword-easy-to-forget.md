# Forgetting `global` on an output silently does nothing

**Where:** `core/tool_api.py:18-32`, all demo tools

The DSL pattern requires every exported function to declare `global y` for each output it writes:

```python
@export("plus")
def plus():
    global result        # easy to forget
    result = str(a + b)
```

If the author forgets `global result`, the assignment creates a function-local `result` that's discarded when the function returns. The module-level `result` keeps its previous value. The button click "succeeds" (no exception, status `OK`), and the outputs widget shows the *previous* result.

This is the worst class of bug: silent, looks correct, and the user has no signal that anything went wrong.

The `goal.txt` file explicitly states the project is for "the creator of a tool [who] should be able to create [tools] without much knowledge of Python and [the] app internals". The `global` keyword is a Python gotcha that surprises even experienced Pythonistas.

## Why it matters

- The most common DSL footgun, encountered the *first* time a new author writes their second function.
- Has zero detection at scan time and zero detection at run time.

## Suggested fix

Two complementary approaches:

1. **Compare before/after**: at `runner._run`, snapshot each output's module-attribute value before calling `fn.callable()`, and again after. If *no* output changed, surface a non-fatal warning ("function `plus` ran but didn't update any output — did you forget `global`?"). Cheap, catches the common case.

2. **Replace globals with a context object**: change the DSL so authors write:

   ```python
   @export("plus")
   def plus(io):
       io.result = str(io.a + io.b)
   ```

   No `global`, no surprise, and the function signature documents which inputs/outputs it touches. Bigger DSL change but kills the foot-gun entirely. (See also issue 07 — both issues have the same root cause: globals as the I/O channel.)

Option 1 is a small, additive fix; option 2 is a real DSL evolution — file separately if the team wants to consider it.
