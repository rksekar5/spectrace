# SpecTrace specification workflow

This repository uses Fission AI OpenSpec 1.14.1 with the `spec-driven` schema and
Codex support. The application implementation has merged. The completed change is archived at
[`bootstrap-spectrace`](changes/archive/2026-10-13-bootstrap-spectrace/proposal.md).

## Canonical specifications and archived change

- [Proposal](changes/archive/2026-10-13-bootstrap-spectrace/proposal.md): motivation and capability scope.
- [Requirement catalog](specs/requirement-catalog/spec.md): OpenSpec input and explicit IDs.
- [Pytest references](specs/pytest-references/spec.md): static, explicit test links.
- [Traceability report](specs/traceability-report/spec.md): mapping, Markdown output, CLI behavior.
- [Design](changes/archive/2026-10-13-bootstrap-spectrace/design.md): assumptions, alternatives, and edge cases.
- [Tasks](changes/archive/2026-10-13-bootstrap-spectrace/tasks.md): implementation and verification checklist.

The canonical specifications preserve the approved requirements and acceptance
scenarios. The archive retains the original proposal, deltas, design, completed
tasks, and [implementation verification](changes/archive/2026-10-13-bootstrap-spectrace/verification.md).

## OpenSpec tooling

OpenSpec requires Node.js 20.19 or newer. On a developer machine, install the pinned
authoring CLI with `npm install -g @fission-ai/openspec@1.14.1`. It is independent of
the Python CLI's runtime dependencies.

In the prepared cloud environment, use:

```bash
cd /workspace/spectrace
export PATH=/workspace/.tools/openspec/node_modules/.bin:$PATH
export OPENSPEC_TELEMETRY=0
export XDG_CONFIG_HOME=/workspace/.config
openspec --version
openspec list --json
openspec validate --all --strict --no-interactive
openspec doctor --json
```

Codex skills were generated with `openspec init --tools codex --profile core` and
are committed under `.agents/skills`:

- `$openspec-propose`: create proposal, specs, design, and tasks.
- `$openspec-explore`: investigate ideas and clarify scope.
- `$openspec-update-change`: revise an existing change.
- `$openspec-verify-change`: verify implementation against the approved artifacts.
- `$openspec-apply-change`: implement an approved change.
- `$openspec-sync-specs`: reconcile approved delta specs with canonical specs.
- `$openspec-archive-change`: archive a completed change.

Codex discovers these skills from the checkout; a session started before
initialization may need to be restarted or refreshed to list them in its UI.
The CLI workflow and generated skill files have been verified independently.

The optional verify workflow was added with `openspec config set profile custom`,
`openspec config set workflows '["propose","explore","apply","update","sync","archive","verify"]'`,
and `openspec update`. The generated skill is committed for other Codex sessions.

The `specs/` directory contains the three canonical capability specifications. OpenSpec's status marks
planning artifacts complete by their presence; it does not approve implementation
or indicate that application tests passed.
