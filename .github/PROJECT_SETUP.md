# Project board & basic workflow

Recommended GitHub Project configuration to manage work for this repository.

Suggested columns:
- Backlog (issues/ideas)
- To do (ready for implementation)
- In progress (active work)
- Review (PR opened)
- Done (merged/closed)

Automation suggestions:
- Automatically add issues to Backlog when labeled `triage`.
- Move PR cards to `Review` when a PR is opened that references the issue.
- Close cards and move to `Done` when PRs are merged.

How to create:
1. Open the repository on GitHub.
2. Click "Projects" > "New project" and choose the board template.
3. Create the columns above and add the automation rules (use the sidebar automation options).

Minimal labels to create: `bug`, `feature`, `enhancement`, `needs-review`, `triage`.
