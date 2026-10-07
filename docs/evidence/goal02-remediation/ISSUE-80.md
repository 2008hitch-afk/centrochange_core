# #80 — Italian accounting presentation

## Final technical checkpoint — 2026-10-07

TECHNICAL PASS for the tested implementation. Overall acceptance: PARTIAL / Owner review pending; issue remains OPEN and PR draft.

Italian native standard expense labels, retained canonical account option, Italian document states and explicit cancelled historical balance: 2 targeted browser checks PASS plus full Finance walkthrough.

See [unified final evidence](../GOAL-02-BACKLOG-2026-10-07.md) for the exact tested candidates, commands, limitations and remaining gates. Earlier pending checkpoints below are historical and superseded by this section.

Static mapping tests PASS; runtime/browser verification pending Wave B candidate. Branch `issue-80/italian-accounting-ui`, base #79. Presentation-only controlled translations for known native standard account labels and accounting states. Account identifiers remain unchanged in option values and API requests; unknown customized accounts retain their precise native name rather than guessing accounting meaning. Italian dates outside technical date inputs. Cancelled invoice detail distinguishes historical native outstanding from a currently payable balance. No accounting/schema change. Owner Finance walkthrough remains required.
