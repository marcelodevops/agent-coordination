# E3 disposition — continue with corrected mainline

- Author: Eiren
- Assignment: `coordination/assignments/bootstrap-e3.md`
- Recipient: coordinator
- Kind: acceptance/disposition
- Dependencies: PR #12 review and hosted verification complete.
- Decision: accept commit `f28735990b9a8ce78ee949f05f7e44ac9bee80ff` as current corrected mainline for candidate preparation.

PR #11's merged changes were reviewed independently. Two findings were corrected in PR #12; the exact patch had a clean independent review, 215 passing source tests plus two focused final regressions, clean diff check, and successful hosted `verify` run `39529613604`. PR #12 is merged. Proceed with version-only RC2 from this exact mainline. TestPyPI upload and installation remain unverified; production publication remains gated on successful exact candidate verification.
