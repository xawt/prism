---
type: review_comment
author: "xawt"
created_at: "2026-04-05T16:53:02Z"
path: "src/prompt-loader.cob"
line: 18
in_reply_to: "001"
---

```diff
@@ -0,0 +1,59 @@
+       IDENTIFICATION DIVISION.
+       PROGRAM-ID. PROMPT-LOADER.
+
+      *> CALL "PROMPT-LOADER" USING BY REFERENCE PL-CONTENT PL-STATUS
+      *>
+      *> PL-CONTENT  PIC X(2000) -- raw prompt text on return
+      *> PL-STATUS   PIC X       -- 'Y' = loaded OK, 'N' = file not found
+      *>
+      *> Caller is responsible for JSON-escaping (e.g. via CONTEXT-MGR).
+
+       ENVIRONMENT DIVISION.
+       INPUT-OUTPUT SECTION.
+       FILE-CONTROL.
+           SELECT PROMPT-FILE
+               ASSIGN TO 'prompts/system-prompt.txt'
+               ORGANIZATION IS LINE SEQUENTIAL
+               FILE STATUS IS WS-FILE-STATUS.
```

fixed
