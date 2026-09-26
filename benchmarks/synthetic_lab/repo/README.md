# Synthetic utility service

Small Python repository with catalog labels, feature configuration, pagination,
and checkout pricing. Dependencies: Python standard library only.

Read ISSUE.md for the current task. Run the full regression suite:

```bash
python -B -m unittest discover -s tests -v
```

Only the current issue is intentionally broken. Other components must continue
to pass. Test files are fixed benchmark infrastructure.
