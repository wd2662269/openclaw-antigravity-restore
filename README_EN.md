# OpenClaw Antigravity Restore Script

One-click restore + patch script for `google-antigravity-auth` (OpenClaw 2026.2.25+).

> Script: `restore_antigravity.py`

## What this script does

It runs 4 steps in order:

1. Restores `google-antigravity-auth` plugin files from OpenClaw Git history
2. Applies compatibility patches to OpenClaw `dist/*.js` (provider detection, SSRF RFC2544, etc.)
3. Updates `~/.openclaw/agents/main/agent/models.json` to add `google-antigravity` provider models
4. Runs `openclaw plugins enable google-antigravity-auth`

## Requirements

- OpenClaw installed globally with npm
- Python 3.9+
- GitHub API access (`gh api` is used internally)
- Backup of OpenClaw install directory is strongly recommended

## Quick start

```bash
python restore_antigravity.py
```

After completion:

```bash
openclaw gateway restart
openclaw models auth login --provider google-antigravity --set-default
```

## How AI/Agents should use this script

You can copy-paste this directly into an AI task:

```text
Task: restore OpenClaw google-antigravity-auth on this machine.
Steps:
1) Read restore_antigravity.py first and confirm which directories will be modified.
2) Back up OpenClaw install directories (dist and extensions).
3) Run: python restore_antigravity.py
4) Verify output includes "✅ 修复完成".
5) Run: openclaw gateway restart
6) Check plugin status: openclaw plugins list
7) If auth is missing, run: openclaw models auth login --provider google-antigravity --set-default
8) Report final status (success/failure + exact failure point).
```

## Safe mode (recommended for production)

Use this low-risk rollout sequence:

1. **Backup first**: `dist/` and `extensions/`
2. **Validate in isolation**: test machine / VM first
3. **Verify patch output**: ensure expected patch points are applied
4. **Restart gateway**: `openclaw gateway restart`
5. **Run smoke test**: `openclaw plugins list` + one real auth/use flow

> Note: There is currently no built-in `--dry-run` flag. Safe mode relies on backup + pre-validation.

## Notes

- This is a patch-style script; re-run it after OpenClaw upgrades.
- It modifies installed package files under `dist`, so understand the operational risk.
- Prefer validating in test environment before production.

## License

MIT
