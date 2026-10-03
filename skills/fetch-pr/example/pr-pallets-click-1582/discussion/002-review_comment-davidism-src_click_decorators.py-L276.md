---
type: review_comment
author: "davidism"
created_at: "2020-06-11T00:35:31Z"
path: "src/click/decorators.py"
line: 276
in_reply_to: null
---

```diff
@@ -279,16 +273,11 @@ def callback(ctx, param, value):
             ver = version
             if ver is None:
                 try:
-                    import pkg_resources
+                    import importlib_metadata
```

This is built in to Python 3.8: https://docs.python.org/3/library/importlib.metadata.html. Try importing the built in first, then try the backport.
