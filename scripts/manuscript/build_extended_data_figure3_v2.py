from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from wtbench.manuscript.extended_data_figure3_v2 import main

if __name__ == "__main__":
    main()
