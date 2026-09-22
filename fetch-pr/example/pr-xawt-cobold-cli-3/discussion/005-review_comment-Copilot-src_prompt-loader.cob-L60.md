---
type: review_comment
author: "Copilot"
created_at: "2026-04-05T16:46:55Z"
path: "src/prompt-loader.cob"
line: 60
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
+
+       DATA DIVISION.
+       FILE SECTION.
+       FD  PROMPT-FILE.
+       01  PROMPT-RECORD       PIC X(500).
+
+       WORKING-STORAGE SECTION.
+       01  WS-FILE-STATUS      PIC XX.
+       01  WS-EOF              PIC X.
+       01  WS-PTR              PIC 9(4).
+
+       LINKAGE SECTION.
+       01  PL-CONTENT          PIC X(2000).
+       01  PL-STATUS           PIC X.
+
+       PROCEDURE DIVISION USING PL-CONTENT PL-STATUS.
+
+       MAIN-PARA.
+           MOVE SPACES TO PL-CONTENT
+           MOVE 'N'    TO WS-EOF
+           MOVE 1      TO WS-PTR
+
+           OPEN INPUT PROMPT-FILE
+           IF WS-FILE-STATUS NOT = "00"
+               MOVE 'N' TO PL-STATUS
+               EXIT PROGRAM
+           END-IF
+
+           PERFORM UNTIL WS-EOF = 'Y'
+               READ PROMPT-FILE
+                   AT END
+                       MOVE 'Y' TO WS-EOF
+                   NOT AT END
+                       STRING FUNCTION TRIM(PROMPT-RECORD) ' '
+                           DELIMITED SIZE
+                           INTO PL-CONTENT WITH POINTER WS-PTR
+               END-READ
```

`STRING ... INTO PL-CONTENT WITH POINTER WS-PTR` has no bounds/overflow handling. If the prompt file exceeds 2000 bytes (or even fewer when separators are added), the pointer can run past `PL-CONTENT` and cause truncation or runtime errors depending on the COBOL runtime. Consider adding `ON OVERFLOW` handling (set a non-'Y' status) and/or stopping reads once `WS-PTR` approaches `LENGTH OF PL-CONTENT`.
