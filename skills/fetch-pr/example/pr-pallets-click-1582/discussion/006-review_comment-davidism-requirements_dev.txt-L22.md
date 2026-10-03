---
type: review_comment
author: "davidism"
created_at: "2020-06-11T01:30:56Z"
path: "requirements/dev.txt"
line: 22
in_reply_to: "003"
---

```diff
@@ -19,6 +19,8 @@ filelock==3.0.12          # via tox, virtualenv
 identify==1.4.16          # via pre-commit
 idna==2.9                 # via requests
 imagesize==1.2.0          # via sphinx
+importlib-metadata==1.6.1  # via importlib-resources, pallets-sphinx-themes, pluggy, pre-commit, pytest, tox, virtualenv
```

Oops, my bad, I meant `pip-compile requirements/tests.in`, not `.txt` (and `dev.in`) :sweat: 
