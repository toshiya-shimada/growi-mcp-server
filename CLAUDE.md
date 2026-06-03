# CLAUDE.md

## Branch Strategy

This repository uses GitHub Flow.

- Do not commit directly to `main`.
- Create a feature branch for every change.
- Use `feat/<short-description>` for feature branches.
- Open a pull request from the feature branch into `main`.
- Merge pull requests with a no-fast-forward merge commit.
- Do not use squash merge or rebase merge for normal feature work.
- Keep `main` deployable and protected from direct commits.

## Expected Workflow

1. Start from the latest `main`.
2. Create a feature branch:

   ```bash
   git switch main
   git pull --ff-only
   git switch -c feat/<short-description>
   ```

3. Commit changes only on the feature branch.
4. Push the branch and open a pull request.
5. Merge into `main` with `--no-ff` after review and verification.

## Local Merge Command

When merging locally, use:

```bash
git switch main
git pull --ff-only
git merge --no-ff feat/<short-description>
git push origin main
```
