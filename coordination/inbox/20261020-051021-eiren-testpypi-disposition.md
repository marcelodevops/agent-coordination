# Eiren disposition — TestPyPI candidate gate

- Assignment: E3 / candidate release sequence
- Intended recipient: Eiren coordinator
- Kind: reviewed disposition
- Decision: E3 source integration is accepted at merged main `93b3a82111472e6d3525da4aea10d02dd4150894`; candidate version PR #9 is accepted at merged main `93fa7c50a38bfe7faadf8778ecd98831b4b28d4f`. Required hosted checks passed and the exact version-only diff was independently reviewed.
- Candidate artifact and workflow build gates passed, but TestPyPI publication remains blocked by missing Trusted Publisher configuration (`invalid-publisher`). TestPyPI currently returns 404 for `0.1.1rc1`.
- Next decision/action: configure the exact TestPyPI Trusted Publisher described in the paired outbox result, then rerun the existing TestPyPI workflow for reviewed SHA `93fa7c50a38bfe7faadf8778ecd98831b4b28d4f`. Continue to candidate install verification, integrated E3 review, and stable PyPI only after the exact candidate is present and verified.
