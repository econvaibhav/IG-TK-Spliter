# Contributing

For a reproducible issue, include the platform, recording dimensions, Python
and FFmpeg versions, command used, relevant log excerpt and the affected clip
interval. Share a small example only when you have permission to do so.

For detector changes, describe the interface cue and its numerical rule, and
compare resulting boundaries with manually checked transitions. Keep raw study
recordings and generated outputs outside version control.

Update `docs/METHOD.md` when changing a rule. Edit the LaTeX source and run
`bash tools/build_diagram.sh` when changing the workflow figure. Changes to files
listed in `SOURCE_MANIFEST.json` also need an intentional checksum update.

No software license has been specified; agree reuse and contribution terms
with the repository owner.
