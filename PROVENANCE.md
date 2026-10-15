# Provenance

What the git history of this repo is and isn't, every change I made to it
while publishing, and the things I said about it here that weren't true. None
of it should depend on nobody looking.

## What happened

- I built this in September 2026 with Claude Code, after
  intercompany-close-agent. None of it existed in 2025.
- The commits were backdated to June–November 2025 as they were made, on my
  instructions, so the history would look like long-running work.
- My design notes of 8 September planned how the history and the repo should
  look, so they would read as hand-written: no commits on the first five days
  of any month, as if I were closing the books; a practitioner's voice in the
  docs with a few rough corners left in; and no repo-wide formatting, so the
  diffs wouldn't look machine-made. None of the 69 backdated commits falls on
  days 1–5. I've dropped all of that.
- I first published it in September 2026 under an earlier account, also named
  gabriel-fin-arch, that I've since deleted; its README badge pointed at that
  copy until 1 October. On 1 October 2026 I pushed it to this account, which I
  opened in 2022 as Maxxym404 and later renamed to gabriel-fin-arch.
- When I moved it here on 1 October I also added three commits dated November
  2025, `8adaa13`, `aad8770` and `3616819`, each removing something that
  contradicted those dates (see below).

What is real: the code, the corpus, the gold set and the design decisions in
them, the model run in the README (see [The model run](#the-model-run)), and
every commit from `4976f2c` (14 October 2026) on, which is as recorded.

## What the history shows because of it

- Code and tooling from 2026 sat in commits dated 2025 in the versions I pushed
  on 1 October: `messages.parse` with adaptive thinking, a lockfile with
  packages published up to 5 September 2026, `astral-sh/setup-uv@v7`, and a
  model run labelled `claude-opus-5`.
- The first commit (`bf27977`, dated 11 June 2025) has a 2026 copyright line,
  the true year, which `aad8770` ("licence year", dated 23 November 2025 and
  first pushed on 1 October 2026) changed to 2025 to match the backdated dates.
  The licence says 2026 again.
- `c5ff62d` (dated 10 July 2025) gets structured output through a forced tool
  call, with a comment calling that "2025 style". That file was written during
  the rewrite of 13 October 2026 to make the commit look like 2025 code. The
  extractor has used `messages.parse` from its first version.

## The force-pushes

Times are UTC, as in the Activity tab, where every "before" commit is still
linked and reachable.

| When | Before → after | What changed |
|---|---|---|
| 2026-10-01 11:55 | `7b204e7` → `094f074` | Removed `uv.lock` from the commit dated 24 August 2025 ("ci, and the lockfile so it installs what I ran" became "ci"). That lockfile had packages published up to 5 September 2026. Also added `uv.lock` to `.gitignore` and changed `astral-sh/setup-uv@v7` (released 7 October 2025) to `@v6` in every commit. |
| 2026-10-13 09:25 | `094f074` → `ecd3328` | Changed the author and committer email on all 69 commits from a personal address to the GitHub noreply one. Dropped the badge change from the commit dated 22 November 2025, which had re-pointed the badge at `Maxxym404/revrec-contract-reviewer`, an earlier username of mine; its message lost "point the badge at this repo". |
| 2026-10-13 14:42 | `ef6a584` → `d5fa7bf` | In every commit, the default model went from `claude-opus-5` to `claude-opus-4-0` (`extract/llm.py`, `.env.example`). From the commit dated 16 November 2025 on, the model in `evals/results/llm.json`, the README and `docs/evaluation.md` went from Claude Opus 5 to Claude Opus 4. The numbers did not change. |
| 2026-10-13 17:05 | `d5fa7bf` → `25093c3` | The extractor in the commits dated 10 July to 25 November 2025 went from `messages.parse(output_format=...)` with adaptive thinking, both 2026 features, to a forced tool call. The corpus PDFs in every commit were re-rendered with a reportlab older than 4.4.6, and the floor became a cap (`>=4.1,<4.4.6`). The structured-outputs reason for the flat wire schema (`extract/schema.py`, the commit dated 16 November 2025 and the changelog) was replaced with a vaguer one about the model dropping fields. The 69 timestamps before October had their seconds changed from `:00` to varied values. The commit dated 13 October 2026 that raised the anthropic floor (`89c3121`, "anthropic floor was 0.40; messages.parse(output_format=) needs 0.77") became `f48de6f`, "extract: move to messages.parse, and raise the anthropic floor to match", which now carries out a move the extractor never needed: it had used `messages.parse` from the start. |
| 2026-10-14 08:37 | `25093c3` → `de862ae` | Renamed the commit dated 24 August 2025 from "ci" to "test: add the first checks draft". No content change. |

Every one of them kept the invented dates. The last three are the ones I
regret most: wherever a commit contradicted its date, I changed the commit,
and the 14:42 one changed what the published results said they were measured
on. The honest fix was to say the dates were invented, which is what this file
does now.

`fbd7cea` puts back the four things the 17:05 rewrite had changed in the
current files: the corpus, the reportlab floor, the schema rationale and two
changelog entries.

## What I said here that wasn't true

| Commit | Where | What it said |
|---|---|---|
| `8adaa13` (dated 22 Nov 2025, first pushed 1 Oct 2026) | `docs/architecture.md` | Replaced "The first project I built in this space is a LangGraph agent", which is true, with "My other project in this space", because the backdated dates made this repo look older than intercompany-close-agent. The sentence is back. |
| `3616819` (dated 25 Nov 2025, first pushed 1 Oct 2026) | commit message, corpus, gold set | "The meridian change order was dated after the study it amends had finished." It wasn't: the agreement it amends runs until database lock, expected in the fourth quarter of 2027. I moved the change order from 14 January 2026 to 14 October 2025 because a contract signed in 2026 didn't fit the backdated history. The original date is back. |
| `4976f2c` (14 Oct 2026) | README | "Imported from an older private workspace in Oct 2026. Commit dates are preserved." Nothing was imported, and the dates were invented. |
| `3af6659` (14 Oct 2026) | README | That I built it between June and November 2025, and that the history was reconstructed when I published it. |
| `e6f4cef` (14 Oct 2026) | README, `docs/evaluation.md`, `extract/llm.py` | That the published model numbers came from Claude Opus 4 in November 2025. |
| `b5d4462` (14 Oct 2026) | README, `docs/evaluation.md`, this file | The same dates; that I hadn't kept a usable git history and rebuilt one from my working copy; that the `claude-opus-5` label was wrong; and that my Anthropic Console usage for November 2025 shows the calls. |
| `b250861` (15 Oct 2026) | README, `docs/evaluation.md`, this file | Kept the Opus 4, November 2025 story and marked the model column unverified. |

My profile README made the same claims about the dates in `4593a4f`,
`8e6ce4f`, `62e8d62` and `e6822c6`.

## Other changes

- **CI runs.** I deleted runs #1 to #10, from the pushes between 1 and 13
  October 2026. The first run left is #11.
- **Email.** The versions pushed on 1 October were committed under a personal
  email address, and those orphaned commits still show it.
- **Contribution graph.** My profile's graph shows 239 commits in 2025 for this
  repo. There was no work on it in 2025: they are the backdated commits,
  counted once for every rewritten version. Only GitHub can rebuild the graph,
  and the ways to remove them myself would mean deleting or hiding these repos,
  which would also remove the evidence this file points at, so I've left it as
  it is and said so here and on my profile.
- **`Co-Authored-By`.** `4976f2c`, the first commit as recorded, was drafted by
  the assistant and has no `Co-Authored-By` line. Every commit after it that the
  assistant drafted has one.

## The model run

The numbers in the README's model column come from a run on Claude Opus 5
(`claude-opus-5`) on 10 September 2026. The run is already in the version I
pushed here on 1 October, and the harness writes the model it calls into
`evals/results/llm.json`, which said `claude-opus-5` until I relabelled it.

On 13 October I changed that label to Claude Opus 4 in a history rewrite, so
that the run would fit the commits backdated to 2025, and the notes I wrote
here on 14 and 15 October defended the change. The label is `claude-opus-5`
again. `llm.json` is otherwise identical to the version I pushed on 1 October.

Claude Opus 5 is still available, so the run can be repeated. The corpus PDFs
and the gold set are again byte-for-byte those of the commit that saved the run
(`7ba5a65`, in the version pushed on 1 October). `llm.json` keeps only the
counts, so the run can't be re-scored against later changes to the code. The
extractor now defaults to Claude Opus 5.5, which hasn't been measured yet.

## How to check

```bash
# every force-push, with the commits before and after it
gh api "repos/gabriel-fin-arch/revrec-contract-reviewer/activity?per_page=100" \
  --jq '.[] | select(.activity_type=="force_push") | [.timestamp, .before[0:7], .after[0:7]] | @tsv'

# the model label in the version pushed on 1 October, and before the 14:42 rewrite
gh api "repos/gabriel-fin-arch/revrec-contract-reviewer/contents/evals/results/llm.json?ref=7b204e7" \
  --jq .content | base64 -d | head -3
gh api "repos/gabriel-fin-arch/revrec-contract-reviewer/contents/evals/results/llm.json?ref=ef6a584" \
  --jq .content | base64 -d | head -3

# where the harness takes that label from
grep -n "model" src/revrec_contract_reviewer/evaluate/__init__.py

# the extractor in the commit dated 10 July 2025, before the 17:05 rewrite
gh api "repos/gabriel-fin-arch/revrec-contract-reviewer/contents/src/revrec_contract_reviewer/extract/llm.py?ref=d5ab303" \
  --jq .content | base64 -d | grep -nE "DEFAULT_MODEL|messages\.parse|adaptive"

# the two commits dated November 2025 that went up on 1 October after the first push
gh api repos/gabriel-fin-arch/revrec-contract-reviewer/compare/52d2fbf...7b204e7 \
  --jq '.commits[] | [.sha[0:7], .commit.author.date, .commit.message] | @tsv'

# the agreement the Meridian change order amends runs to 2027
grep -n "until database lock" -A1 src/revrec_contract_reviewer/corpus/library.py

# the corpus PDFs and gold set against the commit that saved the model run (prints nothing)
git fetch origin 7b204e772dfd62631e6d135d10e2b5e533ba0d43
git diff --stat 7ba5a65 -- 'corpus/*.pdf' evals/gold

# no backdated commit on the first five days of a month
gh api "repos/gabriel-fin-arch/revrec-contract-reviewer/commits?until=2026-10-01T00:00:00Z&per_page=100" \
  --jq '.[].commit.author.date[8:10]' | sort | uniq -c

# this account's earlier username still redirects here
gh api repos/Maxxym404/revrec-contract-reviewer --jq .full_name
```

## From here on

No force-pushes, no deleted CI runs. New commits carry their real dates, and a
`Co-Authored-By` line when the assistant wrote them.
