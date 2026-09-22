---
type: review
author: "copilot-pull-request-reviewer"
created_at: "2026-04-05T16:46:55Z"
state: COMMENTED
---

## Pull request overview

Adds support for loading a system prompt from `prompts/system-prompt.txt` at startup and injecting it as the first `system` message so the model has consistent behavioral constraints.

**Changes:**
- Introduces `PROMPT-LOADER` to read a prompt file at startup.
- Updates `main.cob` to prepend the loaded prompt to the conversation context as a `system` message.
- Extends `CONTEXT-MGR` escaping to handle newline characters for JSON safety.

### Reviewed changes

Copilot reviewed 5 out of 5 changed files in this pull request and generated 5 comments.

<details>
<summary>Show a summary per file</summary>

| File | Description |
| ---- | ----------- |
| src/prompt-loader.cob | New module to read `prompts/system-prompt.txt` into a buffer for startup injection. |
| src/main.cob | Loads the system prompt before entering the chat loop and adds it to the context. |
| src/context-mgr.cob | Updates JSON escaping to include newline handling. |
| prompts/system-prompt.txt | Default system prompt content defining assistant behavior. |
| Makefile | Adds the new module to the build sources. |
</details>



<details>
<summary>Comments suppressed due to low confidence (1)</summary>

**src/context-mgr.cob:61**
* `ESCAPE-PARA` can expand the string (e.g., `\` -> `\\`, `"` -> `\"`, newline -> `\n`) but `WS-ESCAPED` is the same size as the input buffer. Without a destination-length check, `WS-DST-IDX` can exceed 2000 and write past `WS-ESCAPED`. Add a guard (and a defined truncation/error behavior) to prevent out-of-range substring writes.
```
                   WHEN X"0A"
                       MOVE '\' TO WS-ESCAPED(WS-DST-IDX:1)
                       ADD 1 TO WS-DST-IDX
                       MOVE 'n' TO WS-ESCAPED(WS-DST-IDX:1)
                   WHEN OTHER
                       MOVE WS-CHAR TO WS-ESCAPED(WS-DST-IDX:1)
               END-EVALUATE
               ADD 1 TO WS-DST-IDX
```
</details>



---

💡 <a href="/xawt/cobold-cli/new/main?filename=.github/instructions/*.instructions.md" class="Link--inTextBlock" target="_blank" rel="noopener noreferrer">Add Copilot custom instructions</a> for smarter, more guided reviews. <a href="https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot" class="Link--inTextBlock" target="_blank" rel="noopener noreferrer">Learn how to get started</a>.
