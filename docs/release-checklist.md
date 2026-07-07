# Release Checklist

Use this before publishing a GitHub release.

## v0.1.0

- [ ] README explains RePoG in user-friendly language.
- [ ] `docs/why-codex.md` explains the Codex fit.
- [ ] `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and `SECURITY.md` exist.
- [ ] Generic examples exist under `examples/`.
- [ ] Issue templates exist under `.github/ISSUE_TEMPLATE/`.
- [ ] Changelog includes `v0.1.0`.
- [ ] Public checks pass:

  ```bash
  python -m py_compile tools/check_state.py tools/check_player_facing.py tools/snapshot.py
  python tools/check_state.py templates/campaign
  python tools/check_player_facing.py --text "You step into the rain."
  ```

- [ ] Git status is clean except intended release changes.
- [ ] Release notes are reviewed.
- [ ] Tag is created only after maintainer approval:

  ```bash
  git tag v0.1.0
  git push origin main
  git push origin v0.1.0
  ```
