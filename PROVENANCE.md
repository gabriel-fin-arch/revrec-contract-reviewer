# Provenance

What the git history of this repo is and isn't, and every change I made to it
while publishing. None of it should depend on nobody looking.

## What is real

- The code, the corpus, the gold set and the design decisions in them.
- When I worked on it: June to November 2025, and a second pass from July to
  September 2026 that moved the extractor to structured outputs
  (`messages.parse`) with adaptive thinking and made Claude Opus 5 the default.
- Every commit from `4976f2c` (14 October 2026) on, which is as recorded.

## What is reconstructed

I didn't keep a usable git history. The commits before 14 October 2026 were
re-created from my working copy when I published the repo. They follow roughly
the order I built things in, but their dates, times of day, messages and
intermediate contents are approximations, not snapshots of what existed then.

Some things in those commits only make sense in that light:

- The README badge, from the commit dated 13 September 2025 (`b30918f`), points
  at this repo, which was created on 1 October 2026.
- The first commit (`bf27977`, dated 11 June 2025) has a 2026 copyright line,
  which `aad8770` ("licence year") corrects. Both were written while
  reconstructing.
- `c5ff62d` (dated 10 July 2025) gets structured output through a forced tool
  call, with a comment calling that "2025 style". That file was written during
  the rewrite of 13 October 2026, as an approximation of how the 2025 extractor
  worked with Claude Opus 4. It is not the original file.

## The force-pushes

Times are UTC, as in the Activity tab, where every "before" commit is still
linked and reachable.

| When | Before → after | What changed |
|---|---|---|
| 2026-10-01 11:55 | `7b204e7` → `094f074` | Removed `uv.lock` from the commit dated 24 August 2025 ("ci, and the lockfile so it installs what I ran" became "ci"). That lockfile had packages published up to 5 September 2026. Also added `uv.lock` to `.gitignore` and changed `astral-sh/setup-uv@v7` (released 7 October 2025) to `@v6` in every commit. |
| 2026-10-13 09:25 | `094f074` → `ecd3328` | Changed the author and committer email on all 69 commits from a personal address to the GitHub noreply one. Dropped the badge change from the commit dated 22 November 2025, which had re-pointed the badge at `Maxxym404/revrec-contract-reviewer`, an earlier username of mine; its message lost "point the badge at this repo". |
| 2026-10-13 14:42 | `ef6a584` → `d5fa7bf` | In every commit, the default model went from `claude-opus-5` to `claude-opus-4-0` (`extract/llm.py`, `.env.example`). From the commit dated 16 November 2025 on, the model in `evals/results/llm.json`, the README and `docs/evaluation.md` went from Claude Opus 5 to Claude Opus 4. The numbers did not change. |
| 2026-10-13 17:05 | `d5fa7bf` → `25093c3` | The extractor in the commits dated 10 July to 25 November 2025 went from `messages.parse(output_format=...)` with adaptive thinking, both 2026 features, to a forced tool call. The corpus PDFs in every commit were re-rendered with a reportlab older than 4.4.6, and the floor became a cap (`>=4.1,<4.4.6`). The structured-outputs reason for the flat wire schema (`extract/schema.py`, the commit dated 16 November 2025 and the changelog) was replaced with a vaguer one about the model dropping fields. The 69 timestamps before October had their seconds changed from `:00` to varied values. The commit dated 13 October 2026 that raised the anthropic floor (`89c3121`, "anthropic floor was 0.40; messages.parse(output_format=) needs 0.77") became `f48de6f`, "extract: move to messages.parse, and raise the anthropic floor to match", which now carries out a move that had already happened in the 2026 pass. |
| 2026-10-14 08:37 | `25093c3` → `de862ae` | Renamed the commit dated 24 August 2025 from "ci" to "test: add the first checks draft". No content change. |

The pattern in the last three is the one I regret: wherever a commit
contradicted its date, I changed the commit. The honest fix was to say the
dates were wrong, which is what this file does instead.

`fbd7cea` puts back the four things the 17:05 rewrite had changed in the
current files: the corpus, the reportlab floor, the schema rationale and two
changelog entries.

## Other changes

- **CI runs.** I deleted runs #1 to #10, from the pushes between 1 and 13
  October 2026. The first run left is #11.
- **Email.** The versions pushed on 1 October were committed under a personal
  email address, and those orphaned commits still show it.
- **Contribution graph.** GitHub counts the commits of the rewritten-away
  versions as well, so the profile's graph shows about three times the 2025
  activity that this history contains. Only GitHub can rebuild it, and the
  ways to bring the number down myself would mean deleting or hiding these
  repos, so I've left it as it is and explained it here and on my profile.

## The model run

The numbers in the README's model column come from a run on Claude Opus 4 in
November 2025. The first versions I published labelled that run
`claude-opus-5`, a model released in July 2026. That label was wrong. I
corrected it by rewriting the history on 13 October instead of with a normal
commit, which is why the earlier versions still say Opus 5.

I can't prove which label is right. I made the run from an Anthropic account
I no longer have, so there are no usage records I can show. Claude Opus 4 was
retired on 15 June 2026, so the run can't be repeated, and `llm.json` keeps
only the counts, so it can't be re-scored against later changes to the gold
set either. Treat the model column as unverified until it is re-measured on a
current model. The extractor now defaults to Claude Opus 5.5, which hasn't
been measured yet.

## How to check

```bash
# every force-push, with the commits before and after it
gh api "repos/gabriel-fin-arch/revrec-contract-reviewer/activity?per_page=100" \
  --jq '.[] | select(.activity_type=="force_push") | [.timestamp, .before[0:7], .after[0:7]] | @tsv'

# the model label before the 14:42 rewrite
gh api "repos/gabriel-fin-arch/revrec-contract-reviewer/contents/evals/results/llm.json?ref=ef6a584" \
  --jq .content | base64 -d | head -3

# the extractor in the commit dated 10 July 2025, before the 17:05 rewrite
gh api "repos/gabriel-fin-arch/revrec-contract-reviewer/contents/src/revrec_contract_reviewer/extract/llm.py?ref=d5ab303" \
  --jq .content | base64 -d | grep -nE "DEFAULT_MODEL|messages\.parse|adaptive"
```

## From here on

No force-pushes, no deleted CI runs. New commits carry their real dates, and a
`Co-Authored-By` line when the assistant wrote them.
