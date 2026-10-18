# A1 — coordinator review notes

Author: Eiren
Assignment: [A1](../assignments/bootstrap-a1.md)
Intended recipient: Mr.Q
Kind: review feedback
Dependencies: current A1 implementation under inspection
Requested result: fix the canonical write-boundary gaps before acceptance; keep scope within A1 ownership.

The new PurePosixPath normalization catches ./ aliases but does not collapse .. and cannot identify in-root symlink aliases. Both still silently overwrite in a real _write_local call:

- New target: files={README.md: first, dir/../README.md: second}; final README becomes second.
- Existing target (--force): real/ directory and alias -> real symlink; files={real/file.txt: first, alias/file.txt: second}; final real/file.txt becomes second.

Validate the resolved destination plan before the first mkdir/write, retaining lexical and rendered composition checks and containment validation. Detect differing content at the same resolved destination, plus resolved file/ancestor conflicts. Add regression coverage for both. Do not remove the existing outside-target symlink guard.

This feedback file does not itself wake the worker; Eiren will explicitly dispatch follow-up if the current run does not read it.
