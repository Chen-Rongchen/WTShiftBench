# Third-party sources and usage conditions

The root LICENSE applies only to project code covered by that license. It does not automatically cover third-party data, model weights, code, or derived assets.

- Included CellOT source retains its BSD-3-Clause license and author attribution; see `reproducibility/v1.2.0/training/cellot/vendor/cellot/LICENSE`. Execution uses the complete vendor directory in the training ZIP.
- GEO datasets retain their accessions and publication references. Obtain data from [GEO](https://www.ncbi.nlm.nih.gov/geo/); accessions are listed in [DATA_AVAILABILITY.md](../DATA_AVAILABILITY.md). Check each dataset's upstream usage requirements.
- Replogle data: [figshare 20029387](https://figshare.com/articles/dataset/20029387). The project MIT license is not a license for those data.
- Official DepMap files: [download portal](https://depmap.org/portal/download/all/). Releases, ModelIDs, official-file hashes, and extracted-table hashes are recorded separately. Complete official CSV files are not redistributed with the source snapshot.
- Geneformer, scGPT, and other upstream weights are not redistributed by default. Acquisition details follow the frozen checkpoint registries, actual adapters, and upstream licenses.

This inventory identifies sources and responsibility boundaries; it does not assert that redistribution permission has been independently confirmed for every asset. Before distributing complete matrices or staged inputs, check applicable data-use and derivative-distribution conditions. Public availability for download is not, by itself, permission to redistribute.
