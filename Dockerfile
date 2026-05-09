# WTShiftBench reproducibility image (figure-build subset).
#
# Build:
#     docker build -t wtshiftbench:latest .
# Run (interactive, with the host data directory mounted):
#     docker run --rm -it \
#         -v $(pwd)/data:/app/data \
#         -v $(pwd)/reports:/app/reports \
#         -v $(pwd)/figure_build/output:/app/figure_build/output \
#         -v $(pwd)/figures:/app/figures \
#         wtshiftbench:latest
# Then, inside the container:
#     bash reproduce_figures.sh
#
# This image installs the lightweight Python stack used by the public
# figure-reproduction wrappers. It does not include the GEARS / scGPT / Geneformer model
# environments; reproduce those locally via pixi (see pixi.toml) on a host
# with a matching CUDA driver.
FROM continuumio/miniconda3:24.7.1-0

WORKDIR /app

COPY environment.yml /tmp/environment.yml
RUN conda env create -f /tmp/environment.yml \
    && conda clean -afy

SHELL ["conda", "run", "-n", "wtshiftbench", "/bin/bash", "-c"]

COPY . /app

RUN pip install --no-deps -e . || true

ENV PYTHONPATH=/app/src:/app/scripts:/app

CMD ["conda", "run", "--no-capture-output", "-n", "wtshiftbench", "bash"]
