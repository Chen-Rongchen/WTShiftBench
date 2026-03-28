# ruff: noqa: F401
from __future__ import annotations

import importlib
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", message=".*The 'nopython' keyword.*")

__version__ = "0.1.0.post2"

GENE_MEDIAN_FILE = Path(__file__).parent / "gene_median_dictionary_gc104M.pkl"
TOKEN_DICTIONARY_FILE = Path(__file__).parent / "token_dictionary_gc104M.pkl"
ENSEMBL_DICTIONARY_FILE = Path(__file__).parent / "gene_name_id_dict_gc104M.pkl"
ENSEMBL_MAPPING_FILE = Path(__file__).parent / "ensembl_mapping_dict_gc104M.pkl"

GENE_MEDIAN_FILE_30M = Path(__file__).parent / "gene_dictionaries_30m/gene_median_dictionary_gc30M.pkl"
TOKEN_DICTIONARY_FILE_30M = Path(__file__).parent / "gene_dictionaries_30m/token_dictionary_gc30M.pkl"
ENSEMBL_DICTIONARY_FILE_30M = Path(__file__).parent / "gene_dictionaries_30m/gene_name_id_dict_gc30M.pkl"
ENSEMBL_MAPPING_FILE_30M = Path(__file__).parent / "gene_dictionaries_30m/ensembl_mapping_dict_gc30M.pkl"

_LAZY_EXPORTS = {
    "DataCollatorForCellClassification": ("geneformer.collator_for_classification", "DataCollatorForCellClassification"),
    "DataCollatorForGeneClassification": ("geneformer.collator_for_classification", "DataCollatorForGeneClassification"),
    "EmbExtractor": ("geneformer.emb_extractor", "EmbExtractor"),
    "get_embs": ("geneformer.emb_extractor", "get_embs"),
    "InSilicoPerturber": ("geneformer.in_silico_perturber", "InSilicoPerturber"),
    "InSilicoPerturberStats": ("geneformer.in_silico_perturber_stats", "InSilicoPerturberStats"),
    "GeneformerPretrainer": ("geneformer.pretrainer", "GeneformerPretrainer"),
    "TranscriptomeTokenizer": ("geneformer.tokenizer", "TranscriptomeTokenizer"),
    "Classifier": ("geneformer.classifier", "Classifier"),
    "MTLClassifier": ("geneformer.mtl_classifier", "MTLClassifier"),
}

__all__ = sorted(_LAZY_EXPORTS)


def __getattr__(name: str):
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module 'geneformer' has no attribute {name!r}")

    module_name, attr_name = _LAZY_EXPORTS[name]
    module = importlib.import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
