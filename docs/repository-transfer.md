# Repository Transfer Checklist

This repository now lives at `HackEAC/braver-tz`.

## Current remote

```bash
git remote set-url origin git@github.com:HackEAC/braver-tz.git
git remote -v
```

## Post-transfer checks

1. Confirm that GitHub redirects the old URL to the new owner.
2. Verify org-side repository settings:
   - GitHub Actions enabled
   - branch protection rules
   - required secrets and variables
   - release permissions
   - admin access for the intended maintainers
3. Do not recreate the previous repository path, because that breaks GitHub's redirect from the transferred repository.
4. Update any remaining references that still point to the old owner, including:
- clone commands
- release links
- Homebrew tap references
- badges or status URLs

Run these local sanity checks:

```bash
git fetch origin
python3 braver.py --help
python3 -m unittest discover -v
```
