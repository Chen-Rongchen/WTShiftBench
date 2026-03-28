from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.stage1a.adapters.scgpt.build_k562_predictions import main


if __name__ == "__main__":
    main()
