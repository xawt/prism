---
type: review_comment
author: "davidism"
created_at: "2020-06-11T00:38:17Z"
path: "requirements/dev.txt"
line: 22
in_reply_to: null
---

```diff
@@ -19,6 +19,8 @@ filelock==3.0.12          # via tox, virtualenv
 identify==1.4.16          # via pre-commit
 idna==2.9                 # via requests
 imagesize==1.2.0          # via sphinx
+importlib-metadata==1.6.1  # via importlib-resources, pallets-sphinx-themes, pluggy, pre-commit, pytest, tox, virtualenv
```

It looks like you added `importlib-resources` to `dev.in` but forgot to commit that. We don't need importlib-resources, just importlib-metadata, and it should be added to `tests.in`, then the relevant `.txts` should be recompiled with `pip-compile requirements/test.txt` and `pip-compile requirements/dev.txt`.
