---
type: review_comment
author: "0x1za"
created_at: "2020-06-11T01:46:59Z"
path: "src/click/decorators.py"
line: 276
in_reply_to: "007"
---

```diff
@@ -279,16 +273,11 @@ def callback(ctx, param, value):
             ver = version
             if ver is None:
                 try:
-                    import pkg_resources
+                    import importlib.metadata
```

Yes definitely, forgot to backport.
