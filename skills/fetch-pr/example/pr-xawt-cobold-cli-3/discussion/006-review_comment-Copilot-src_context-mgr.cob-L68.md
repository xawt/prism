---
type: review_comment
author: "Copilot"
created_at: "2026-04-05T16:46:55Z"
path: "src/context-mgr.cob"
line: 68
in_reply_to: null
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

JSON strings cannot contain literal control characters like tab (X"09") or carriage return (X"0D"); currently only backslash/quote/newline are escaped. Since this paragraph is responsible for producing valid JSON, consider adding escapes for at least tab (`\t`) and carriage return (`\r`) as well.
