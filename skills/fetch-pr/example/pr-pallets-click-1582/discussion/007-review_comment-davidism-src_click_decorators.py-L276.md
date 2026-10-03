---
type: review_comment
author: "davidism"
created_at: "2020-06-11T01:34:18Z"
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
+                    import importlib.metadata
```

Still need to fall back to `importlib_metadata` if this fails, since we support 3.6+.

```python
try:
    from importlib.metadata import version as get_version
except ImportError:
    try:
        from importlib_metadata import version as get_version
    except ImportError:
        get_version = None

if get_version is not None:
    ver = get_version(prog)
```
