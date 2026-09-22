---
type: review_comment
author: "xawt"
created_at: "2026-04-05T17:00:24Z"
path: "src/context-mgr.cob"
line: 68
in_reply_to: "006"
---

```diff
@@ -51,6 +51,10 @@
                        MOVE '\' TO WS-ESCAPED(WS-DST-IDX:1)
                        ADD 1 TO WS-DST-IDX
                        MOVE '"' TO WS-ESCAPED(WS-DST-IDX:1)
+                   WHEN X"0A"
+                       MOVE '\' TO WS-ESCAPED(WS-DST-IDX:1)
+                       ADD 1 TO WS-DST-IDX
+                       MOVE 'n' TO WS-ESCAPED(WS-DST-IDX:1)
                    WHEN OTHER
                        MOVE WS-CHAR TO WS-ESCAPED(WS-DST-IDX:1)
                END-EVALUATE
```

fixed
