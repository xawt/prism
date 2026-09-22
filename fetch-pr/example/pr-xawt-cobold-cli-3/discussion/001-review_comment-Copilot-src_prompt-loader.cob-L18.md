---
type: review_comment
author: "Copilot"
created_at: "2026-04-05T16:46:54Z"
path: "src/prompt-loader.cob"
line: 18
in_reply_to: null
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

`ASSIGN TO 'prompts/system-prompt.txt'` makes the prompt path depend on the current working directory. The rest of the app (e.g., ENV-READER) resolves configuration relative to the executable path, so running `dist/cobold` from another directory will silently skip the system prompt. Consider computing the prompt file path dynamically (relative to the executable or an env var) and using `ASSIGN TO DYNAMIC`.
