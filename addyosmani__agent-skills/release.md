tag: 0.6.12
name: Agent Skills 0.6.12
published_at: 2026-10-03T06:42:02Z
prerelease: False

Agent Skills 0.6.12 is mostly about skills saying the right thing. It fixes a spec workflow that ran past its own approval gate, removes a command that does not exist and a code sample that does not parse, and slims performance-optimization the same way 0.6.11 slimmed security-and-hardening.

## Skill fixes

- **spec-driven-development stops after the spec** (#629, @nucliweb, fixes #622). On hosts that load only the skill, some models ran Specify, Plan, Tasks and Implement in one turn, because the explicit "confirm before proceeding" step lived only in the `/spec` command. The skill now ends the turn after saving the spec and waits for approval, the same fix #497 made for interview-me.
- **No more invented rollback command** (#628, @jsynowiec). The shipping-and-launch checklist told you to run `npx prisma migrate rollback`, which Prisma does not have. It now asks for your project's verified rollback command or runbook, whatever migration tool you use.
- **The idempotency example parses** (#627, @jsynowiec). A bare `throw;` in api-and-interface-design is a syntax error in JavaScript; it now rethrows the caught error.
- **performance-optimization is slimmer** (#580, @Syamsuddin, with fixes from @nucliweb's review). Step 3's code patterns moved into a skill-local `references/optimization-patterns.md`, taking SKILL.md from 496 to 267 lines. The condensed summary keeps the guidance that matters without opening the reference: when an index will not help and what to do instead (partial, trigram or expression indexes), that a bad `rows=` estimate means `ANALYZE` rather than a new index, and stating a cache's staleness window.
- **code-review-and-quality answers its own regression question** (#618, @CybotTM): invert one condition the change adds, run the suite, and report a mutation that stays green as a missing test.
- The ADR template's Status line now starts at Proposed, matching the lifecycle below it (#615, @mavericksea-ai).

## Host guides (withdrawn on main)

This release shipped setup guides for Oh My Pi (#617) and Dojo Workspace (#616). Both were withdrawn on main in #641: they were merged ahead of community host guides that had waited longer, and no maintainer had run either host. CONTRIBUTING now has a written bar for host guides. Oh My Pi is listed as one line in `docs/other-hosts.md`.

## Tooling

- **Anchors in reference links are checked** (#626, @nucliweb, fixes #625). Renaming a heading in a reference file used to break every `#anchor` link to it while CI stayed green. The validator now resolves anchors with GitHub's slug rules.
- The floor-guard reference no longer mistakes an added `++` line or a removed `--` line for a file header, and it runs from the top of the work tree so untracked files outside a subfolder are not missed (#614, @mavericksea-ai).
- Frontmatter values that start with a YAML indicator are rejected (#603, @abhisheksharma2411), and so are top-level frontmatter keys outside the spec, with the per-agent configuration guide now linked from CONTRIBUTING, the README and skill-anatomy (#608, @ayobamiseun).
- Every plugin eval grader counts the slash-command path as well as the skill (#613, @federicobartoli).

## Thanks

Thanks to everyone who contributed and reviewed this release: @nucliweb, @jsynowiec, @andrebrait, @un33k, @mavericksea-ai, @federicobartoli, @CybotTM, @ayobamiseun, @abhisheksharma2411, and @Syamsuddin.

**Full Changelog**: https://github.com/addyosmani/agent-skills/compare/0.6.11...0.6.12

