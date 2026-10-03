---
type: issue_comment
author: "davidism"
created_at: "2020-06-24T21:34:47Z"
---

Squashed the original commits, added a changelog, added a change to `requirements/tests.in` that didn't get committed before. Then, while reviewing this, I realized that the entire function could use a refactor and new docs, so I did that in a separate commit.

* `option()` returns a decorator, so there's no point in wrapping it in another decorator internally.
* Version detection relies on being able to detect the module defining the CLI by examining the stack frames. Added the `package_name` parameter to skip or override detection if it fails. Also make `package` available in the message format, since it can be different than `prog`.
* Use `inspect.currentframe()` for stack inspection instead of a private method. Gets the top-level package name instead of the full dotted `__name__`.
* Use Python 3's `nonlocal` keyword for modifying args from the callback.
* Only try to detect the version if a package name was given or detected.
* Show a specific error if `importlib_metadata` needs to be installed.
* Show an error if `metadata.version()` can't find the package. This can happen if the package name doesn't match the PyPI name.
* Show the detected package name in the error message when the version wasn't detected, to make it clearer what Click was trying.

Also noticed that the change you made changed how the version was being detected, from looking at entry points to looking at the package name directly. It looks like the values returned by `importlib.metadata.entry_points()` aren't linked to the distributions that own them, so there's not really a nice way to use the previous implementation. Writing some notes below so the difference is clear later.

---

The previous implementation tried to find the program name among the `console_scripts` entry points, then if the module that entry pointed at matched the stack frame detected module, it took the version of the distribution that created the entry. The new implementation skips looking at entry points and assumes the package name is the same as the installed name. While that's not strictly true, it's definitely a good and common practice. The previous implementation wasn't strictly correct either, as there was no guarantee that the module that created the version option was also the one pointed to by the entry point.
