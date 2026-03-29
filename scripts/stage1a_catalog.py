try:
    from scripts.stage1a.benchmark_invariant.catalog import *  # noqa: F401,F403
except ModuleNotFoundError:
    from stage1a.benchmark_invariant.catalog import *  # noqa: F401,F403
