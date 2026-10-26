# Provenance

What the git history of this repo is and isn't, every change I made to it
while publishing, and the things I said about it here that weren't true. None
of it should depend on nobody looking.

On 15 October 2026 I rewrote the history one last time to put back the real
commit times; [Restoring the real dates](#restoring-the-real-dates) says how.
Unless a section says otherwise, the SHAs in this file are from the history as
it stood before that. They are still reachable (`git fetch origin <sha>`), the
force-pushes are linked from the Activity tab, and the [commit map](#commit-map)
gives the new SHA for each.

## What happened

- I built this in September 2026 with Claude Code, after
  intercompany-close-agent. None of it existed in 2025.
- The commits were backdated to June–November 2025 on my instructions, so the
  history would look like long-running work, and the default branch kept
  those dates until 15 October 2026.
- My design notes of 8 September planned how the history and the repo should
  look, so they would read as hand-written: no commits on the first five days
  of any month, as if I were closing the books; a practitioner's voice in the
  docs with a few rough corners left in; and no repo-wide formatting, so the
  diffs wouldn't look machine-made. None of the 69 backdated commits fell on
  days 1–5. I've dropped all of that.
- I first published it in September 2026 under an earlier account, also named
  gabriel-fin-arch, that I've since deleted; its README badge pointed at that
  copy until 1 October. On 1 October 2026 I pushed it to this account, which I
  opened in 2022 as Maxxym404 and later renamed to gabriel-fin-arch.
- When I moved it here on 1 October I also added three commits dated November
  2025, `8adaa13`, `aad8770` and `3616819`, each removing something that
  contradicted those dates (see below).
- On 15 October 2026 I put the real times back, from my Claude Code session
  logs. Of the 69 commits I pushed here on 1 October, 54 were made on 8
  September 2026, 47 of them by a single script run; 8 on 9 September, 4 on
  10 September and 3 on 1 October.

What is real: the code, the corpus, the gold set and the design decisions in
them, and the model run in the README (see [The model run](#the-model-run)).
Since 15 October 2026 the history is too: every commit's author date is the
time it was made. The commits from 14 October 2026 on (`4976f2c` and after)
always had their real dates.

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
| 2026-10-15 | `da26a44` → the current `main` | Restored the real dates: every commit of the version pushed on 1 October, the commits as pushed on 13 October and every one pushed since, rebuilt on its own tree with its own message and the time it was made as its author date, with what each earlier force-push changed in the files recorded as a bridge commit. No file changed. See [Restoring the real dates](#restoring-the-real-dates). |

The first five kept the invented dates. The three of 13 October 14:42, 17:05
and 14 October are those I regret most: wherever a commit contradicted its
date, I changed the commit, and the 14:42 one changed what the published
results said they were measured on. The honest fix was to say the dates were
invented, which this file did from 14 October, and then to put the real ones
back, which the last one did.

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
  email address, and those orphaned commits still show it. The restored
  history uses the GitHub noreply address throughout.
- **Contribution graph.** The graph used to show 239 commits in 2025 for this
  repo, counted once for every rewritten version. GitHub has recounted it:
  measured on 26 October 2026 (GraphQL `contributionsCollection`), it shows no
  commits in 2025 and only the default-branch work in 2026. The orphaned
  commits were left in place, so the SHA links in this file still resolve.
- **`Co-Authored-By`.** `4976f2c`, the first commit as recorded, was drafted by
  the assistant and has no `Co-Authored-By` line. Every commit after it that the
  assistant drafted has one. None of the commits before it has one.

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

## Restoring the real dates

Until 15 October 2026 this file said the dates were invented, but the history
still carried them, and so did my contribution graph. So I rewrote the default
branch one last time, to make the history itself true rather than only the note
about it.

**Where the times come from.** My Claude Code session logs record every
`git commit` the assistant ran. Each commit's author date is now the time the
tool call that made it returned, to the second (git stores whole seconds).
Where several commits came from one call, they share its time. The commit map
below gives the source of every date.

**Author date and committer date.** The author date is when the commit was
made. The committer date is when I rebuilt the history, so it is 15 October
2026 on every commit. `git log --format='%ad | %cd'` shows both.

**Nothing in the files changed.** Each commit was rebuilt with `git
commit-tree` on the tree of the commit it replaces, with its message byte for
byte:

1. the 69 commits of the version pushed here on 1 October (`7b204e7`);
2. a bridge commit for each of the force-pushes of 1 October 11:55 and 13
   October 09:25;
3. the 11 commits pushed on 13 October, as they were pushed that day, so
   `89c3121` is back as "anthropic floor was 0.40; messages.parse(output_format=)
   needs 0.77" and not the `f48de6f` the 17:05 rewrite made of it;
4. a bridge commit for each of the force-pushes of 13 October 14:42 and 17:05;
5. the 10 commits from 14 October on, unchanged.

A bridge commit is dated at its force-push, is titled "history: what the
force-push of … changed", and has the tree that force-push left, so `git show`
on it shows exactly what the rewrite did to the files. The force-push of 14
October 08:37 left the files as they were and has no bridge; what each
force-push changed in older commits is in [the table above](#the-force-pushes).

Author and committer are `Gabriel S. <121440470+gabriel-fin-arch@users.noreply.github.com>`
throughout.

### Before 1 October

This file didn't list how the history was made before I first pushed here:

- **8 September, 07:52–07:53 UTC.** The first 47 commits were made by one run
  of a script the assistant wrote that morning, which built the history out of
  the finished code. It added the files in stages, with dates from 13 June to
  7 September 2026. To show five fixes as fixes, it first wrote back pre-fix
  versions of `extract/rules.py`, `models/judgment.py` and `corpus/library.py`,
  made by editing the finished code. So those commits' trees are stages of the
  finished code, not snapshots of work in progress, and they all have the same
  author date, 07:53:48 UTC. The script ran three times in two minutes; the
  second and third runs started by deleting the repository's `.git`, and the
  third is the history that was kept.
- **8 to 10 September.** The next 19 commits were made in eleven tool calls,
  with their dates forced to other times between 8 and 10 September.
- **1 October, 10:39 UTC.** `git filter-repo` re-dated the 67 commits there
  were to 11 June–22 November 2025, with dates from a script that picked days
  at random and skipped the first six days of each month. One commit made a
  minute earlier lost its real date that way. Then I pushed it here.

### What the real dates show

54 commits on 8 September 2026 (47 of them in the same second, by the script
above); 8 on 9 September; 4 on 10 September; 3 on 1 October. The lockfile in
"ci, and the lockfile so it installs what I ran" has packages published up to
10:42 UTC on 5 September, and that commit is now dated 8 September. The repo
was created on the earlier account on 9 September at 12:33 UTC, after the
first 62 commits.

### Commit map

<details>
<summary>Every commit: new SHA, its version pushed on 1 October, its version
in <code>main</code> until 15 October, author date and source (94
rows)</summary>

| New | 1 October | In `main` until 15 October | Author date (UTC) | Source |
|---|---|---|---|---|
| `24c411d` | `7d10fe9` | `bf27977` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `1617749` | `f00f633` | `bfa3d92` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `fc068ab` | `74b123a` | `ff6d8f0` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `6a3077d` | `16c2e11` | `4f09322` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `c04ce89` | `64203c3` | `72179bc` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `b130b68` | `d45633c` | `5ad047b` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `af610da` | `df3f439` | `d2ffe7f` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `3d22b0d` | `ccaaabc` | `f35c8a8` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `6f990c6` | `53c20a5` | `b79b6fc` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `eefb70d` | `a88f588` | `724a554` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `c8720cf` | `5a777ae` | `34dc5cb` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `17113e9` | `0d31d95` | `827e4f2` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `e8d9795` | `2a4319a` | `369d5b1` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `e65647a` | `4588ddd` | `400ee39` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `30facd6` | `54f3f0d` | `d0c6264` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `0402eda` | `9a2d669` | `9a98624` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `2d5d765` | `5b7948f` | `9c1970a` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `2e567e9` | `03993ca` | `ae42018` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `13fab68` | `a36475c` | `5d2ac89` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `85eedb4` | `aff6655` | `c5ff62d` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `068e39f` | `36547be` | `05229e9` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `c5b5d37` | `6c4a958` | `4f620dd` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `3d17cce` | `d3f7475` | `1e83be4` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `e5914a1` | `c1c08ca` | `60ebb21` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `11ccd79` | `41ec920` | `75f2c44` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `f16475c` | `180dcba` | `cbadeda` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `06e26ed` | `c755e83` | `80bc18c` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `18566d7` | `e61cf15` | `dff2bac` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `b338b73` | `4366fe0` | `ba9a46e` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `b27f557` | `95fbecc` | `26fdc7b` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `546d433` | `ff8ab66` | `5472e4b` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `b5e3d0d` | `5d34c35` | `ac521d4` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `a36c423` | `efdcdb5` | `c882273` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `c677c33` | `c56e003` | `6b9c057` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `6899afc` | `128f5e6` | `e9237d4` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `94d623b` | `339aefe` | `adabb8c` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `ff17283` | `8e3e2ec` | `3b283e9` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `53b400b` | `feb8bb5` | `5be2352` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `039fa40` | `727a234` | `f64e0d4` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `50e93ab` | `f337263` | `435b38a` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `816f872` | `1155084` | `1b00fab` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `780b922` | `762e41d` | `31bd31b` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `3e208dd` | `d66c61b` | `5474988` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `e9a89ea` | `fdbc66c` | `f2767ba` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `b8610d9` | `e3074ba` | `976c68b` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `a7c0bca` | `f2f29fc` | `b30918f` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `3b1928a` | `b67f339` | `fae5f7c` | 2026-09-08 07:53:48 | Claude Code session log, one script call at 07:53:48 UTC that made 47 commits |
| `d46cf56` | `25021ea` | `e8eb2b9` | 2026-09-08 07:55:12 | Claude Code session log, tool call at 07:55:12 UTC |
| `509941c` | `5f153cc` | `85f7ea2` | 2026-09-08 07:57:35 | Claude Code session log, tool call at 07:57:35 UTC |
| `c1666e3` | `0dab9d7` | `443d9f0` | 2026-09-08 11:47:23 | Claude Code session log, tool call at 11:47:23 UTC (4 commits in one call) |
| `ab8d49d` | `01afda0` | `f49faaf` | 2026-09-08 11:47:23 | Claude Code session log, tool call at 11:47:23 UTC (4 commits in one call) |
| `00b0721` | `c23fe3c` | `60528e7` | 2026-09-08 11:47:23 | Claude Code session log, tool call at 11:47:23 UTC (4 commits in one call) |
| `fa43469` | `72032f9` | `c2a8f1f` | 2026-09-08 11:47:23 | Claude Code session log, tool call at 11:47:23 UTC (4 commits in one call) |
| `f63040b` | `a347667` | `23b4b13` | 2026-09-08 12:00:28 | Claude Code session log, tool call at 12:00:28 UTC |
| `b9fa9b5` | `87197b8` | `6cb3a20` | 2026-09-09 12:18:45 | Claude Code session log, tool call at 12:18:45 UTC (2 commits in one call) |
| `ce810a7` | `629dbc8` | `fe5bf82` | 2026-09-09 12:18:45 | Claude Code session log, tool call at 12:18:45 UTC (2 commits in one call) |
| `04c097c` | `54f83f2` | `ad93ca0` | 2026-09-09 12:20:18 | Claude Code session log, tool call at 12:20:18 UTC |
| `4ba0291` | `75dadf1` | `174acb9` | 2026-09-09 12:23:33 | Claude Code session log, tool call at 12:23:33 UTC (3 commits in one call) |
| `e4f0421` | `786f345` | `82fec02` | 2026-09-09 12:23:33 | Claude Code session log, tool call at 12:23:33 UTC (3 commits in one call) |
| `f610eff` | `544dd1f` | `bfb1237` | 2026-09-09 12:23:33 | Claude Code session log, tool call at 12:23:33 UTC (3 commits in one call) |
| `3bf3988` | `9431f13` | `f13b4c1` | 2026-09-09 12:25:10 | Claude Code session log, tool call at 12:25:10 UTC |
| `961abdd` | `17975e1` | `f103fde` | 2026-09-09 12:33:10 | Claude Code session log, tool call at 12:33:10 UTC |
| `7a39a72` | `4c5a7eb` | `9d9dfc4` | 2026-09-10 08:56:31 | Claude Code session log, tool call at 08:56:31 UTC (2 commits in one call) |
| `a46a855` | `7ba5a65` | `6797152` | 2026-09-10 08:56:31 | Claude Code session log, tool call at 08:56:31 UTC (2 commits in one call) |
| `a25e95d` | `3b6faab` | `58dd78b` | 2026-09-10 09:04:21 | Claude Code session log, tool call at 09:04:21 UTC (2 commits in one call) |
| `fa84a52` | `0d20539` | `3d3a9ac` | 2026-09-10 09:04:21 | Claude Code session log, tool call at 09:04:21 UTC (2 commits in one call) |
| `c4158fc` | `52d2fbf` | `8adaa13` | 2026-10-01 10:39:08 | Claude Code session log, tool call at 10:39:08 UTC |
| `e4d7cc5` | `414ccd5` | `aad8770` | 2026-10-01 11:32:44 | Claude Code session log, tool call at 11:32:44 UTC (2 commits in one call) |
| `1ed182f` | `7b204e7` | `3616819` | 2026-10-01 11:32:44 | Claude Code session log, tool call at 11:32:44 UTC (2 commits in one call) |
| `fa3038b` | — | — | 2026-10-01 11:55:56 | bridge: Activity, force-push at 11:55:56 UTC leaving `094f074` |
| `2676a5c` | — | — | 2026-10-13 09:25:54 | bridge: Activity, force-push at 09:25:54 UTC leaving `ecd3328` |
| `2ecee99` | — | `f48de6f` | 2026-10-13 11:08:05 | unchanged; content and message as pushed on 13 October (`89c3121`) |
| `bd5b478` | — | `0bc8ba7` | 2026-10-13 11:44:52 | unchanged; content and message as pushed on 13 October (`8b93bfa`) |
| `1123986` | — | `ad761f9` | 2026-10-13 11:47:29 | unchanged; content and message as pushed on 13 October (`5fa52b4`) |
| `3c21c16` | — | `8d0dbad` | 2026-10-13 11:48:55 | unchanged; content and message as pushed on 13 October (`11fe7b9`) |
| `f4a16c4` | — | `c9cad24` | 2026-10-13 11:50:35 | unchanged; content and message as pushed on 13 October (`7e69982`) |
| `dc835cf` | — | `af1c993` | 2026-10-13 11:53:46 | unchanged; content and message as pushed on 13 October (`ff464ad`) |
| `022f049` | — | `07a6d67` | 2026-10-13 11:55:16 | unchanged; content and message as pushed on 13 October (`f01ac39`) |
| `d9a76e1` | — | `5a476df` | 2026-10-13 11:55:32 | unchanged; content and message as pushed on 13 October (`a272399`) |
| `c2bf2a5` | — | `1affd19` | 2026-10-13 11:58:12 | unchanged; content and message as pushed on 13 October (`224c7ed`) |
| `110ea7d` | — | `06e6f82` | 2026-10-13 12:31:50 | unchanged; content and message as pushed on 13 October (`14577ad`) |
| `1c6b4f3` | — | `de862ae` | 2026-10-13 12:31:51 | unchanged; content and message as pushed on 13 October (`ef6a584`) |
| `1e3ed0d` | — | — | 2026-10-13 14:42:38 | bridge: Activity, force-push at 14:42:38 UTC leaving `d5fa7bf` |
| `1a4b11c` | — | — | 2026-10-13 17:05:58 | bridge: Activity, force-push at 17:05:58 UTC leaving `25093c3` |
| `3dfd1f6` | — | `4976f2c` | 2026-10-14 10:08:44 | unchanged |
| `9c044bb` | — | `3af6659` | 2026-10-14 13:08:18 | unchanged |
| `73b8d94` | — | `e6f4cef` | 2026-10-14 13:36:25 | unchanged |
| `02ed220` | — | `fbd7cea` | 2026-10-14 14:26:35 | unchanged |
| `585e520` | — | `b5d4462` | 2026-10-14 14:30:38 | unchanged |
| `36c1eb3` | — | `b250861` | 2026-10-15 07:05:42 | unchanged |
| `6876205` | — | `10a319a` | 2026-10-15 07:56:03 | unchanged |
| `5a86e5c` | — | `400d3b1` | 2026-10-15 08:20:49 | unchanged |
| `7d3a310` | — | `e9dfa57` | 2026-10-15 12:25:24 | unchanged |
| `f2d6ae7` | — | `da26a44` | 2026-10-15 12:46:38 | unchanged |

</details>

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

# no backdated commit on the first five days of a month, in the history before
# the restoration
gh api "repos/gabriel-fin-arch/revrec-contract-reviewer/commits?sha=de862ae98684c1b972e063411b6f6005d2c70172&until=2026-10-01T00:00:00Z&per_page=100" \
  --jq '.[].commit.author.date[8:10]' | sort | uniq -c

# this account's earlier username still redirects here
gh api repos/Maxxym404/revrec-contract-reviewer --jq .full_name
```

The restoration of 15 October, from a clone. `f2d6ae7`, `1ed182f` and the four
bridges are rebuilt commits; the other SHAs are from before it and need
fetching first:

```bash
git fetch origin da26a44a6c0641910a80eab16143c23edd4f2fb6 \
  7b204e772dfd62631e6d135d10e2b5e533ba0d43 \
  094f074bc4e872a5778551298f9ec61234e288a3 ecd3328e9da6359faa073847fd23cf39e3a07992 \
  d5fa7bf01bc1e41a5a4375e3dfb9ab747a70fa70 25093c36d73dd6fb69510f339907ea0e1f5908fb

# no file changed: the last commit before the restoration and the last rebuilt
# one have the same tree (prints nothing)
git diff da26a44 f2d6ae7

# the 69 commits pushed on 1 October: same trees and messages, in order (prints nothing)
diff <(git log --reverse --format='%T %s' 7b204e7) <(git log --reverse --format='%T %s' 1ed182f)
diff <(git log --reverse --format=%B 7b204e7) <(git log --reverse --format=%B 1ed182f)

# each bridge has the tree its force-push left (four pairs of equal lines)
git rev-parse fa3038b^{tree} 094f074^{tree} 2676a5c^{tree} ecd3328^{tree} \
  1e3ed0d^{tree} d5fa7bf^{tree} 1a4b11c^{tree} 25093c3^{tree}

# when each commit was made, and when the history was rebuilt
git log --reverse --format='%h %ad | %cd | %s' --date=iso main
```

## From here on

No force-pushes, no deleted CI runs. The restoration of 15 October 2026 was the
one exception, made only to put the real dates back, and there won't be
another. New commits carry their real dates, and a `Co-Authored-By` line when
the assistant wrote them.
