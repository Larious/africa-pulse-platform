# Leadership Briefing

`generate_leadership_deck.py` creates `Africa_Pulse_Live_Platform_Briefing.pptx` from the running local ClickHouse warehouse. It is intentionally generated from live mart and run-control data so the deck does not drift from the working system.

Run it after ClickHouse is running:

```bash
/Users/mac/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 presentation/generate_leadership_deck.py
```

Use `docs/technical-defense-runbook.md` as the presenter reference for questions that need deeper engineering detail.
