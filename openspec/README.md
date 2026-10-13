# SpecTrace specification workflow

This repository uses Fission AI OpenSpec 1.14.1 with the `spec-driven` schema and
Codex support. The application implementation is under review. The active change is
[`bootstrap-spectrace`](changes/bootstrap-spectrace/proposal.md).

## Review the change

- [Proposal](changes/bootstrap-spectrace/proposal.md): motivation and capability scope.
- [Requirement catalog](changes/bootstrap-spectrace/specs/requirement-catalog/spec.md): OpenSpec input and explicit IDs.
- [Pytest references](changes/bootstrap-spectrace/specs/pytest-references/spec.md): static, explicit test links.
- [Traceability report](changes/bootstrap-spectrace/specs/traceability-report/spec.md): mapping, Markdown output, CLI behavior.
- [Design](changes/bootstrap-spectrace/design.md): assumptions, alternatives, and edge cases.
- [Tasks](changes/bootstrap-spectrace/tasks.md): implementation and verification checklist.

Implementation was explicitly approved after the specification PR merged. Keep
this change unarchived and do not merge the implementation PR automatically.

## OpenSpec tooling

OpenSpec requires Node.js 20.19 or newer. On a developer machine, install the pinned
authoring CLI with `npm install -g @fission-ai/openspec@1.14.1`. It is independent of
the future Python CLI's runtime dependencies.

In the prepared cloud environment, use:

```bash
cd /workspace/spectrace
export PATH=/workspace/.tools/openspec/node_modules/.bin:$PATH
export OPENSPEC_TELEMETRY=0
export XDG_CONFIG_HOME=/workspace/.config
openspec --version
openspec status --change bootstrap-spectrace
openspec validate bootstrap-spectrace --strict --no-interactive
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

The `specs/` directory is intentionally empty until implementation and the approved
archive workflow establish canonical specifications. OpenSpec's status marks
planning artifacts complete by their presence; it does not approve implementation
or indicate that application tests passed.
