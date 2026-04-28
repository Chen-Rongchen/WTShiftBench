#!/usr/bin/env Rscript
# Pre-ranked fgsea wrapper for the pathway-response exploratory layer.
#
# Replaces the project-internal Python `prerank_fgsea` (which had a hash-based
# seed reproducibility bug and only supported fixed-permutation testing) with
# the canonical R Bioconductor fgsea (Korotkevich et al., Nat Methods 2021).
#
# Inputs:
#   --ranking-tsv    TSV with columns: gene, score (header required, no order assumed)
#   --gmt            Path to GMT file (e.g. MSigDB Hallmark h.all.symbols.gmt)
#   --output-tsv     Output path for fgsea results
#   --min-size       Minimum post-intersection set size (default 10)
#   --max-size       Maximum post-intersection set size (default 500)
#   --eps            Adaptive multilevel boundary; smaller -> higher precision (default 1e-10)
#   --n-perm-simple  Initial permutation count for multilevel pre-test (default 10000)
#   --seed           RNG seed for reproducibility (default 42)
#
# Output TSV columns:
#   pathway, ES, NES, pval, padj, log2err, size, n_genes_in_set,
#   direction, leading_edge
#
# Usage:
#   Rscript run_fgsea.R --ranking-tsv ranking.tsv --gmt hallmark.gmt \
#       --output-tsv out.tsv --eps 1e-10 --n-perm-simple 10000 --seed 42

suppressMessages({
  library(fgsea)
  library(data.table)
})

# ---- argparse (no external dep) ----
parse_args <- function(argv) {
  defaults <- list(
    `ranking-tsv`   = NULL,
    `gmt`           = NULL,
    `output-tsv`    = NULL,
    `min-size`      = "10",
    `max-size`      = "500",
    `eps`           = "1e-10",
    `n-perm-simple` = "10000",
    `seed`          = "42"
  )
  i <- 1L
  while (i <= length(argv)) {
    key <- sub("^--", "", argv[i])
    if (i + 1L > length(argv)) stop(sprintf("Missing value for %s", argv[i]))
    defaults[[key]] <- argv[i + 1L]
    i <- i + 2L
  }
  required <- c("ranking-tsv", "gmt", "output-tsv")
  for (k in required) {
    if (is.null(defaults[[k]])) stop(sprintf("Missing required arg --%s", k))
  }
  defaults
}

args <- parse_args(commandArgs(trailingOnly = TRUE))

ranking_path  <- args[["ranking-tsv"]]
gmt_path      <- args[["gmt"]]
output_path   <- args[["output-tsv"]]
min_size      <- as.integer(args[["min-size"]])
max_size      <- as.integer(args[["max-size"]])
eps           <- as.numeric(args[["eps"]])
n_perm_simple <- as.integer(args[["n-perm-simple"]])
seed          <- as.integer(args[["seed"]])

cat(sprintf("[fgsea] ranking=%s\n", ranking_path))
cat(sprintf("[fgsea] gmt=%s\n", gmt_path))
cat(sprintf("[fgsea] output=%s\n", output_path))
cat(sprintf("[fgsea] minSize=%d maxSize=%d eps=%g nPermSimple=%d seed=%d\n",
            min_size, max_size, eps, n_perm_simple, seed))

# ---- load inputs ----
rank_dt <- fread(ranking_path, sep = "\t", header = TRUE)
required_cols <- c("gene", "score")
if (!all(required_cols %in% names(rank_dt))) {
  stop(sprintf("ranking-tsv must contain columns: %s", paste(required_cols, collapse = ", ")))
}
# de-duplicate genes by max |score| if any duplicates appear
if (anyDuplicated(rank_dt$gene)) {
  cat(sprintf("[fgsea] WARNING: %d duplicate gene rows; keeping max-|score| per gene\n",
              sum(duplicated(rank_dt$gene))))
  rank_dt[, abs_score := abs(score)]
  setorder(rank_dt, gene, -abs_score)
  rank_dt <- rank_dt[, .SD[1L], by = gene]
  rank_dt[, abs_score := NULL]
}
ranking <- setNames(as.numeric(rank_dt$score), rank_dt$gene)
ranking <- sort(ranking, decreasing = TRUE)

# Load GMT (returns named list of character vectors)
pathways <- gmtPathways(gmt_path)

# Pre-compute n_genes_in_set (GMT-original size) and intersection size
n_genes_in_set_map <- vapply(pathways, length, integer(1))
intersected_sizes <- vapply(pathways, function(g) sum(g %in% names(ranking)), integer(1))

# ---- run fgsea ----
set.seed(seed)
fres <- fgsea(
  pathways    = pathways,
  stats       = ranking,
  minSize     = min_size,
  maxSize     = max_size,
  eps         = eps,
  nPermSimple = n_perm_simple
)

if (nrow(fres) == 0L) {
  cat("[fgsea] WARNING: empty result; writing empty TSV\n")
  empty <- data.table(
    pathway = character(),
    ES = numeric(), NES = numeric(),
    pval = numeric(), padj = numeric(), log2err = numeric(),
    size = integer(), n_genes_in_set = integer(),
    direction = character(), leading_edge = character()
  )
  fwrite(empty, output_path, sep = "\t")
  quit(save = "no", status = 0L)
}

# ---- format output ----
fres[, direction := fifelse(NES > 0, "up", fifelse(NES < 0, "down", "neutral"))]
fres[, n_genes_in_set := n_genes_in_set_map[pathway]]
fres[, leading_edge := vapply(leadingEdge, function(g) paste(g, collapse = ";"), character(1))]
fres[, leadingEdge := NULL]

setcolorder(fres, c(
  "pathway", "ES", "NES", "pval", "padj", "log2err",
  "size", "n_genes_in_set", "direction", "leading_edge"
))

fwrite(fres, output_path, sep = "\t")

cat(sprintf("[fgsea] Wrote %d rows to %s\n", nrow(fres), output_path))
cat(sprintf("[fgsea] padj < 0.10: %d  | < 0.05: %d  | < 0.01: %d\n",
            sum(fres$padj < 0.10, na.rm = TRUE),
            sum(fres$padj < 0.05, na.rm = TRUE),
            sum(fres$padj < 0.01, na.rm = TRUE)))
