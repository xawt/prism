---
type: issue_comment
author: "davidism"
created_at: "2020-06-24T22:25:51Z"
---

Incorporated #1531 for better version detection when using `python -m package`. Also noticed that the original code wasn't breaking the reference cycle on `frame`, so fixed that.
