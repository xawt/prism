```
██████╗ ██████╗ ██╗███████╗███╗   ███╗
██╔══██╗██╔══██╗██║██╔════╝████╗ ████║
██████╔╝██████╔╝██║███████╗██╔████╔██║
██╔═══╝ ██╔══██╗██║╚════██║██║╚██╔╝██║
██║     ██║  ██║██║███████║██║ ╚═╝ ██║
╚═╝     ╚═╝  ╚═╝╚═╝╚══════╝╚═╝     ╚═╝
```

*Split the diff like light through a prism — see instantly what needs your eyes and what you can hand to the model.*

```
                    ╱▏
        PR     ────╱ ▏────▶ 🔴  needs a human's eyes
               ───╱  ▏───▶ 🟠
               ──╱   ▏──▶ 🟡
                ╱    ▏─▶ 🟢
               ╱     ▏▶ 🔵  safe to hand to the model
              ╱      ▏▶ 🟣
```

> **Status:** early-stage project, no implementation in this repository yet.

## How it works

1. Prism analyzes the change using one of the following engines:
   - **Jev** — a model from TypeSafe AI
   - a classic LLM (e.g. Claude, GPT)
2. The analysis results are aggregated into a checklist for the reviewer.
3. Each checklist item is tagged with one of two statuses:
   - **Needs human attention** — risky, ambiguous spots, or ones requiring business/domain context.
   - **Can be handed to the model** — mechanical, repetitive changes that are easy to verify automatically.

Goal: the reviewer spends time on the parts that actually need it, instead of reviewing the whole diff uniformly.

## Test engines

Prism is designed so the analysis engine (Jev vs. classic LLM) is interchangeable — the choice of engine shouldn't change the format of the output checklist.

## Output

A checklist split into "needs manual review" and "can be verified by a model" sections, ready to paste as a PR comment or use locally before sending a review.

## Roadmap

- [ ] Integration with Jev (TypeSafe AI)
- [ ] Integration with a classic LLM as an alternative engine
- [ ] Checklist format (markdown / PR comment)
- [ ] First CLI-runnable version of the tool
