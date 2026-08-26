# Contributing

Thanks for considering a contribution — this project depends on community eyes
on the data (that's its whole honesty model; see spec §12).

## Report a wrong or outdated entry

- **Best:** open a GitHub **Issue** describing what's wrong. If you're looking at
  a facility on the map, include its name — one issue per facility keeps review quick.
- Every correction needs a **verifiable source** (press release, official page,
  operator announcement). "I heard" isn't enough — corrections are verified
  before they're accepted (spec §14).

## Propose changes (PRs)

1. **Data changes:** include the source for every number you add/change. Rows
   stay honest: confirmed vs estimated is labeled deliberately — don't upgrade
   an estimate without a source.
2. **Code changes:**
   - Branch off `main` (phase branches track the roadmap in `docs/milestones/`).
   - Run tests before opening: `python3 -m unittest discover -s tests` (stdlib, no deps).
   - Keep pipeline additions stdlib-only where reasonable; runtime deps belong in
     `requirements.txt` and are used only inside `.venv`/Actions.
   - New provider/source config belongs in config files (`data/sources.json`,
     `scripts/llm/providers.py`), never hardcoded mid-function.
3. **Licensing:** code contributions are MIT; data contributions must be
   ODbL-compatible (see `LICENSE-DATA.md`).

## Review flow

Corrections (issues/PRs) enter the same **Pending** review queue as the
automation's findings; a human approves everything before it reaches Main and
the public map. Expect a question if a source can't be verified.
