---
name: flowdiff
description: Review a git diff, pull request, branch, or patch file by drawing the runtime flows it touches as interactive flowcharts or sequence diagrams. One node per function, colored added/modified/removed/unchanged, click a node to see the exact hunk and reviewer notes. Use this whenever someone asks to review, explain, visualize, summarize, or understand a PR, diff, changeset, or commit range, asks "what does this PR actually change", "walk me through this diff", "how does the request flow change", or wants a diagram, flowchart or sequence diagram of code changes, even if they never say "flowchart". Outputs a standalone HTML page plus Mermaid markdown that renders in GitHub and GitLab comments.
---

# flowdiff

A diff is a list of hunks. A reviewer thinks in flows: "a request enters here, passes through these functions, and this is where behaviour changed." This skill draws those flows with the change overlaid, and attaches the real hunk to each node so the picture can be checked against the code.

The order matters: understand the flow as it exists first, then overlay the diff. A diff shows what moved, not what it sits between. Reading diff-first is how a reviewer misses the sibling branch that now behaves differently, or the caller the PR forgot.

## Steps

1. **Get the diff into a file.** Whichever applies:
   ```bash
   gh pr diff 123 > pr.diff          # a PR
   git diff main...HEAD > pr.diff    # a branch
   git diff > pr.diff                # uncommitted work
   ```
   If the user handed you a `.patch` or `.diff`, use it as is.

2. **List the changed functions.** `grep -n '^diff --git\|^@@' pr.diff` shows files and hunk positions. Hunk headers name the enclosing definition only for top-level ones, so open each file at the hunk and name the function or method yourself. Tests, docs, config, lockfiles, and pure renames do not become nodes. They go in the top-level `other` list.

3. **Find each flow and read it as it was.** For each changed function, grep for callers upward until you reach an entry point: a route handler, CLI command, job, event handler, UI action, or exported API. Each entry point is one flow. Now read the entry point's whole body on the base revision (`git show main:path/to/file`, or the pre-patch source) and write down the sequence of calls it makes, down to the effect that matters: a DB write, a network call, the response. That sequence is the skeleton of the flow. Do this before looking at the hunks again.

   Then choose the diagram for this flow. Count the separate components the skeleton crosses: processes, services, queues, datastores, external APIs.
   - One component, or the change is about paths and branches: a flowchart, the default.
   - Two or more components, and the PR changes what they say to each other, in what order, or moves work from one to another (sync to async, a new worker, a webhook, a retry): set `"type": "sequence"`.

   Say which you chose and why in the flow's `description`. "Keeping a flow reviewable" below has the rules for each type.

4. **Overlay the diff.** Mark each function in the skeleton `added`, `modified`, `removed`, or `unchanged`. When a call is rerouted, keep the old path as a `removed` edge and draw the new one as `added`, so the reader sees both the before and the after in one picture. A changed function reached from two entry points appears in both flows.

5. **Widen the frame.** Three checks that the diff cannot do for you:
   - Grep every caller of every changed function. A caller that is not drawn in this flow goes in the node's `callers` list. An empty list means you checked and found none. This is where a stale signature, a cron job, or a test helper nobody updated shows up.
   - An unchanged function that reads or writes data the PR changed (a new field, a new return value, a new exception) belongs in the flow with a `notes` entry explaining why, even though it has no hunk. Data stored before the change is a classic: a new nullable field means old rows take the other branch.
   - Write the flow's `description` for someone outside the PR: who triggers this entry point, and what the flow promises when it finishes.

6. **Number the risks.** A risk is something that can go wrong in production because of this PR: a race, a lost message, a caller that now breaks, data that takes the wrong branch. For each one write a `risks` entry on the flow with a short `title` stating the failure, a `severity`, a `detail` giving the concrete sequence that triggers it, and a `fix` when a small one exists. Then point at it: add the risk's `id` to the `risks` list of every node, function or edge where it happens. The renderer numbers the risks across the review, prints the number on the diagram coloured by severity, and lists them beside it, so the reader sees where each problem sits in the flow. In a sequence flow the number is drawn on messages only, so put every risk on the message where it happens; a risk on a function there shows only when the participant is clicked.
   - `high`: loses or corrupts data, breaks an existing caller, or opens a security hole. `medium`: wrong behaviour a user can hit. `low`: worth knowing, not worth blocking.
   - A risk that is not on any diagram, such as a broken import in an untouched file, still gets an entry; say where it is in `detail`.
   - `notes` are for context that is not a failure: what an external system guarantees, why an unchanged node is drawn.
   - Skip this step only when the user asked to understand a change and not to review it. No risks found is a valid result: leave `risks` out and say so in the reply.

7. **Write `flows.json`.** Fields are listed below, and `references/example.json` is a complete one built from a small Python diff. Read it before writing your first. The fields that carry the review:
   - `change`: the behavioural delta in 12 words or fewer. "retries 3× on gateway timeout", not "added a for loop".
   - `notes`: context a reviewer needs that is not a failure. Failures go in `risks` (step 6). Leave it out when there is nothing to say.
   - `callers`: call sites not drawn in this flow (see step 5). Required on every changed function.

   `diff` is the hunk text for that function, copied from `pr.diff`. Trim it to the function. Nodes with no hunk leave it out.

8. **Render and open.**
   ```bash
   python3 <this skill>/scripts/render.py flows.json -o review.html --md review.md
   open review.html        # macOS; xdg-open on Linux, start on Windows
   ```
   The script validates first and exits non-zero naming the problem. Fix and rerun.

9. **Reply.** One line per flow: what changes and its highest-severity risk by number, then the path to `review.html`. If the user wants a PR comment, give them `review.md`. Its Mermaid blocks render natively on GitHub and GitLab.

## Keeping a flow reviewable

- **4 to 12 nodes.** The skeleton from step 3 sets the shape. Collapse a run of unchanged calls that nothing in the PR touches into its last node, but keep every unchanged node that step 5 pulled in.
- **Nodes are functions.** Not files, not classes, not lines. Label with the name a reader would grep for: `charge()`, `POST /orders`, `OrderService.save`.
- **Edges are calls or data handoffs,** drawn in the order a request meets them. Edges into and out of an added node are `added`; the path they replace is `removed`. The renderer draws these thick and dotted so the reader sees the shape of the change before reading anything.
- **Decision nodes only for branches the PR adds or changes.** Every `if` in the codebase is not a diamond.
- **Flowchart for control flow inside a component, sequence for collaboration between components.** The default is a flowchart: nodes are functions, and it shows paths and branches. Set `"type": "sequence"` on a flow when the change is about how separate components work together over time: a client, a service, a queue, a database, an external API, with retries, races, async callbacks, or a reply that now arrives in a different order. In a sequence flow:
  - Participants are components, not functions. Label the participant with the component (`Orders API`) and list every function the PR changes inside it under `functions`, each with its own status, change, notes, callers and diff. The box shows them prefixed `+` added, `~` modified, `-` removed, and clicking it shows each function's hunk. The box itself stays neutral; the colour of each function line carries the status. Only components that run the PR's code carry functions. A database, a queue or an external API is a participant with no functions: a changed data-access helper such as `get_user()` goes under the component that calls it in this flow, not under the table it reads.
  - Edges are messages, listed top to bottom in time order. Include the replies that matter.
  - No decision nodes; put the condition in the message label.
  - If every participant would live in the same process, it is a call chain: draw a flowchart instead.
- **One flow per entry point.** If a PR touches a helper used by eight entry points, draw the two or three that matter most, list the rest in that node's `callers`, and say so in `summary`.

## flows.json

```
title        string            page title, e.g. "PR #412: coupons and refunds"
summary      string            two or three sentences on what the PR does
other        [string]          changes that are not part of any flow (tests, config, deps)
flows        [flow]
  id           string          short slug
  title        string          tab label, e.g. "Create order"
  description  string          who triggers this flow, what it promises, what changed in it
  type         flowchart | sequence   optional, default flowchart
  direction    "TD" | "LR"     optional, default TD, flowchart only
  nodes        [node]
    id           string        unique within the flow
    label        string        function name as a reader would grep for it; in a sequence flow, the component
    status       added | modified | removed | unchanged   (default unchanged)
    shape        step | decision | entry | store           (default step)
    file         string        path, optional
    line         number        optional
    change       string        behavioural delta, 12 words or fewer, shown inside the node
    notes        string | [string]   reviewer observations, shown highlighted
    callers      [string]      call sites not drawn in this flow; required on changed functions, [] if none
    diff         string        unified-diff hunk text for this function
    risks        [risk id]     risks that happen here; also allowed on a function and on an edge
    functions    [function]    sequence participants only: the changed functions inside this component;
                               each has label, status, file, line, change, notes, callers, diff as above
  edges        [edge]
    from, to     node ids
    label        string        optional, e.g. "on success"
    status       added | removed | unchanged   (default unchanged)
    risks        [risk id]
  risks        [risk]          numbered across the review in the order written
    id           string        unique within the flow, e.g. "enqueue-before-commit"
    title        string        the failure, in one line
    severity     high | medium | low
    detail       string        the concrete sequence that triggers it
    fix          string        optional
```

## Files

- `scripts/render.py` validates `flows.json`, builds the Mermaid source, writes `review.html` and, with `--md`, Mermaid markdown. Python 3, stdlib only.
- `assets/template.html` is the page: flow tabs, the diagram, a side panel with the clicked function's hunk, notes and undrawn callers, a light/dark toggle, and a Copy Mermaid button for pasting into a PR. It loads Mermaid from a CDN, so it needs network to render.
- `references/example.json` is a complete worked example; `references/example-review.html` is what it renders to.
- `references/example-sequence.json` is a sequence flow: a blocking charge replaced by an async webhook, where the review finding is a race.
