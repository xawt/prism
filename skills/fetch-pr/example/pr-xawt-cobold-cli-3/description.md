## 📌 What
Load a system prompt from `prompts/system-prompt.txt` at startup and inject it as the first `system`
message in the conversation context.

## 🤔 Why
Without a system prompt the model has no persona or behavioural constraints. Loading it from a plain
text file keeps it editable without recompiling.

## 🛠️ Changes
Added new module:

- `src/prompt-loader.cob` – reads `prompts/system-prompt.txt` line by line and returns raw text to
  the caller; escaping is left to `CONTEXT-MGR` to avoid double-processing

Modified:

- `src/main.cob` – calls `PROMPT-LOADER` before the chat loop and passes result to `CONTEXT-MGR`
  with role `system`
- `src/context-mgr.cob` – extended `ESCAPE-PARA` to escape newlines (`X"0A"` → `\n`) so multi-line
  file content produces valid JSON
- `Makefile` – added `src/prompt-loader.cob` to the build

Added:

- `prompts/system-prompt.txt` – default system prompt defining the agent persona

## 🧪 How to test
Build and run with:

```bash
make
dist/cobold
```

Expected behaviour: the agent responds as **cobold** with a concise style defined by the system
prompt. To verify the prompt is active, ask *"who are you?"*.

If `prompts/system-prompt.txt` is missing, startup continues without a system message (silent
fallback).

