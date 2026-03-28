"""Stage 1A entrant recipes.

延迟导入各个 entrant adapter 以避免环境依赖问题。
每个 adapter 只能在满足其依赖的环境中导入。
"""

__all__ = ["GEARSEntrant", "ScGPTEntrant", "GeneformerEntrant"]


def __getattr__(name: str):
    if name == "GEARSEntrant":
        from wtbench.entrants.gears_adapter import GEARSEntrant

        return GEARSEntrant
    if name == "ScGPTEntrant":
        from wtbench.entrants.scgpt_adapter import ScGPTEntrant

        return ScGPTEntrant
    if name == "GeneformerEntrant":
        from wtbench.entrants.geneformer_adapter import GeneformerEntrant

        return GeneformerEntrant
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
