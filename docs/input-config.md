# Input config (`prism.yaml`)

The input config is a YAML file with the list of questions Prism asks about a pull request. For each
question Prism builds a prompt from the question text and the context you select, sends it to an
engine, and checks that the answer has the expected type.

The context comes from a PR directory created by the [`fetch-pr`](../skills/fetch-pr/SKILL.md)
skill (e.g. `skills/fetch-pr/example/pr-pallets-click-1582/`). By default Prism reads the config
from `./prism.yaml`.

> **Status:** this describes the first, minimal version of the format. Only questions about the
> whole PR (`per: pr`) are supported. See [Not yet supported](#not-yet-supported).

## Simple example

```yaml
version: 1
questions:
  - id: description_matches_diff
    per: pr
    type: yesno
    good: "yes"
    question: "Does the PR description accurately reflect the actual changes?"
    context:
      - pr.description
      - commits[*].diff
```

### Dissection

```yaml
version: 1
```

Format version. Must be `1`.

```yaml
questions:
```

The list of questions. Each item is one question. Prism asks them in the order they appear.

```yaml
  - id: description_matches_diff
```

A unique name for the question. Prism uses it in results and error messages. Use `snake_case`.

```yaml
    per: pr
```

Sets what the answer is about and how many times Prism asks the question. `pr` means one answer
for the whole pull request, so the question is asked once. `pr` is currently the only allowed
value.

```yaml
    type: yesno
```

The answer type. `yesno` is a yes/no question. The engine does not return a plain yes or no. It
returns the probability that the answer is "yes", a number from `0` to `1`. For example, `0.9`
means "almost certainly yes" and `0.5` means "can't tell".

```yaml
    good: "yes"
```

Required for `yesno`. Sets which answer is the good outcome:

- `"yes"`: a high probability is good. Example: *"Does the description match the changes?"*
- `"no"`: a high probability is bad. Example: *"Does the change touch error handling?"*

This lets Prism treat "low means bad" the same way for every question, however it is worded.
Put the value in quotes. Without them, YAML reads a bare `yes` as the boolean `true`.

```yaml
    question: "Does the PR description accurately reflect the actual changes?"
```

The question sent to the engine. Write it in English and keep it general ("this PR", "this
change"). The context supplies the details.

```yaml
    context:
      - pr.description
      - commits[*].diff
```

The data from the PR directory that goes into the prompt. Each entry is a **selector**:

- `pr.description` is the PR description (`description.md`).
- `commits[*].diff` is the diff of every commit in the PR, in order (`diffs/*.diff`). `[*]` means
  "all commits".

The selectors are added to the prompt in the order you list them.

Write `context` as a list with one `- ` item per line, as shown here. Don't use the one-line form
`[a, b]`. In that form YAML reads `[` inside `commits[*]` as the start of a nested list and `*` as
an alias, so the file fails to parse unless every such selector is in quotes.

## Larger example

This is the development config in [`prism.yaml`](../prism.yaml). It has one question of each
answer type.

```yaml
version: 1
questions:
  - id: pr_scope
    per: pr
    type: choice
    question: "What is the dominant nature of this change?"
    options: [feature, fix, refactor, config, docs, mixed]
    context:
      - pr.meta
      - pr.description
      - commits[*].message

  - id: review_load
    per: pr
    type: score
    range: [1, 5]
    rubric:
      1: "Trivial: docs, formatting, config only."
      3: "Moderate logic change with clear intent."
      5: "Large or subtle change across public API, needs deep review."
    question: "How much cognitive effort does reviewing this PR require?"
    context:
      - pr.meta
      - commits[*].diff

  - id: description_matches_diff
    per: pr
    type: yesno
    good: "yes"
    question: "Does the PR description accurately reflect the actual changes?"
    context:
      - pr.description
      - commits[*].diff
```

### Dissection

The last question is the one from the simple example. Only the parts that are new are described
here.

#### `pr_scope`: a `choice` question

```yaml
    type: choice
    options: [feature, fix, refactor, config, docs, mixed]
```

`choice` sorts the PR into one category. `options` is required and must be a non-empty list of
unique values. The engine returns exactly one of them, and any other value is rejected. Choose
categories that don't overlap. If they can overlap, add a catch-all option like `mixed`.

```yaml
    context:
      - pr.meta
      - pr.description
      - commits[*].message
```

This question uses two more selectors:

- `pr.meta` is the PR metadata from `meta.json`: title, author, branches, labels and change counts.
- `commits[*].message` is the headline and body of every commit from `commits.json`, **without
  diffs**. It is much cheaper than `commits[*].diff` when the messages are enough.

#### `review_load`: a `score` question

```yaml
    type: score
    range: [1, 5]
```

`score` is a rating on a scale. `range: [min, max]` is required and `min` must be smaller than
`max`. The engine returns a number within the range, including both ends.

```yaml
    rubric:
      1: "Trivial: docs, formatting, config only."
      3: "Moderate logic change with clear intent."
      5: "Large or subtle change across public API, needs deep review."
```

`rubric` is optional. It describes what selected values on the scale mean. You don't need to
describe every value, and the engine places answers between the ones you describe. Every key must
be inside `range`. A rubric keeps answers consistent between runs and between engines, so use one
whenever the scale isn't obvious.

### Answer types at a glance

| `type` | Type-specific fields | Engine returns | Example answer |
|---|---|---|---|
| `yesno` | `good: "yes" \| "no"` (required) | probability of "yes", `0`–`1` | `0.15` |
| `choice` | `options` (required) | one of `options` | `refactor` |
| `score` | `range` (required), `rubric` (optional) | number in `range` | `4` |

### Selectors at a glance

| Selector | What it contains | Source in the PR directory |
|---|---|---|
| `pr.meta` | title, author, branches, labels, additions/deletions | `meta.json` |
| `pr.description` | PR description | `description.md` |
| `commits[*].message` | headline and body of every commit, no diffs | `commits.json` |
| `commits[*].diff` | diff of every commit, in order | `diffs/*.diff` |

## Validation

Prism checks the config before it asks any question. It stops with an error that names the
question and the field when:

- `version` is missing or isn't `1`;
- an `id` is missing or is used more than once;
- `per` isn't `pr`;
- `type` isn't `yesno`, `choice` or `score`;
- a field required by the `type` is missing: `good` for `yesno`, `options` for `choice`, `range`
  for `score`;
- `good` isn't `"yes"` or `"no"`;
- `options` is empty or has duplicates;
- `range` isn't two numbers with `min < max`, or a `rubric` key is outside `range`;
- `context` is empty or has an unknown selector;
- a question has a field not described here. This catches typos like `optons`.

## Not yet supported

These are planned but not part of the format yet. A config that uses them is rejected.

- `per: commit`, `per: file`, `per: thread`: asking a question once per commit, per changed file,
  or per review thread, with selectors like `commit.diff` or `file.diffs`.
- Selectors for review discussion, such as `pr.discussion` and `thread.comments`.
- `role` (`triage` / `check` / `info`), `route`, `fail_if` / `warn_if`: turning answers into
  checklist statuses.
- `engine`: choosing the engine for each question.
