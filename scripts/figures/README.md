# Figure builders

These are the stable publication-facing figure entry points. Run them from the
repository root through the Pixi `core` environment.

```bash
pixi run --environment core python scripts/figures/build_figure3.py --panels-only
```

Builders consume repository-relative analysis outputs and write editable SVG
panels plus source tables under `figures/`. Local caches, assembled figures and
raster exports are ignored by Git.

`materialize_extended_data_figure1.py` prepares the dataset-profile and
target-gene readout inputs required by Extended Data Figure 1 from locally
acquired public datasets.
