from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.stage1a.benchmark_invariant.scoring.validate_prediction_contract import main


if __name__ == "__main__":
    main()
