"""CLI entrypoint for `python3 -m dashboard`."""
from __future__ import annotations

import sys
from dashboard.server import main

if __name__ == "__main__":
    sys.exit(main())
