#!/usr/bin/env Rscript
# SCP542 RDS → CSV/TSV 转换脚本
# 关键发现：ccle 是 per-cell-line NMF（198株细胞系，每株独立30个程序）
# 输出目录：data/baselines/scp542/

suppressPackageStartupMessages(library(methods))

SCP542_DIR <- file.path(Sys.getenv("WTBENCH_ROOT", getwd()), "data/baselines/scp542")
OUT_DIR    <- SCP542_DIR

message("=== SCP542 RDS Converter ===")

# ── 1. nmf_w_basis_ccle: gene loadings per cell line ──────────────────────
# Each element: genes x programs matrix for one cell line
# We'll extract the CCLE-wide union and stack all programs
message("\n[1/5] nmf_w_basis_ccle.RDS ...")
w_all <- readRDS(file.path(SCP542_DIR, "nmf_w_basis_ccle.RDS"))
message("  cell lines: ", length(w_all))

# Extract HCC38 and HCC1143 W matrices directly (our primary lines)
for (cl in c("HCC38_BREAST", "HCC1143_BREAST")) {
  if (cl %in% names(w_all)) {
    m <- w_all[[cl]]
    out_file <- file.path(OUT_DIR, paste0("nmf_w_", gsub("_", "-", tolower(cl)), ".tsv"))
    rownames(m) <- make.names(rownames(m), unique=TRUE)
    write.table(
      data.frame(gene = rownames(m), m, check.names = FALSE),
      out_file, sep = "\t", row.names = FALSE, quote = FALSE
    )
    message("  ", cl, " (genes x programs): ", dim(m)[1], " x ", dim(m)[2],
            " → ", basename(out_file))
  } else {
    message("  WARNING: ", cl, " not found in nmf_w_basis_ccle")
  }
}

# Also save a gene×program matrix for a merged version (union of top-loading genes per program)
# Get all unique genes across cell lines
all_genes <- unique(unlist(lapply(w_all, function(m) rownames(m))))
message("  total unique genes across lines: ", length(all_genes))

# Save cell line list
cl_df <- data.frame(cell_line = names(w_all), n_programs = sapply(w_all, function(m) ncol(m)))
write.table(cl_df, file.path(OUT_DIR, "cell_lines.tsv"), sep = "\t", row.names = FALSE, quote = FALSE)
message("  → cell_lines.tsv (", nrow(cl_df), " lines)")

# ── 2. nmf_h_coef_ccle: cell program scores per cell line ─────────────────
message("\n[2/5] nmf_h_coef_ccle.RDS ...")
h_all <- readRDS(file.path(SCP542_DIR, "nmf_h_coef_ccle.RDS"))
message("  cell lines: ", length(h_all))

# Extract HCC38 and HCC1143 H matrices
for (cl in c("HCC38_BREAST", "HCC1143_BREAST")) {
  if (cl %in% names(h_all)) {
    m <- h_all[[cl]]
    colnames(m) <- make.names(colnames(m), unique=TRUE)
    out_file <- file.path(OUT_DIR, paste0("nmf_h_", gsub("_", "-", tolower(cl)), ".tsv"))
    write.table(
      data.frame(cell_barcode = rownames(m), m, check.names = FALSE),
      out_file, sep = "\t", row.names = FALSE, quote = FALSE
    )
    message("  ", cl, " (programs x cells): ", dim(m)[1], " x ", dim(m)[2],
            " → ", basename(out_file))
  }
}

# ── 3. nmf_programs_sig_ccle.RDS: 50 genes x 800 programs (gene sets) ───
message("\n[3/5] nmf_programs_sig_ccle.RDS ...")
prog <- readRDS(file.path(SCP542_DIR, "nmf_programs_sig_ccle.RDS"))
cat("  matrix dim:", paste(dim(prog), collapse=" x "), "\n")
# Rows = max 50 genes per program; Cols = 800 programs
# Transpose to: program_id | gene1,gene2,... (one row per program)
n_progs <- ncol(prog)
max_genes <- nrow(prog)
prog_lines <- lapply(seq_len(n_progs), function(j) {
  genes <- prog[, j]
  genes <- genes[nchar(genes) > 0 & !is.na(genes)]
  paste0("program_", j, "\t", paste(genes, collapse = ","))
})
writeLines(unlist(prog_lines), file.path(OUT_DIR, "nmf_programs_sig_ccle.tsv"))
message("  → nmf_programs_sig_ccle.tsv (", n_progs, " programs, up to ", max_genes, " genes each)")

# ── 4. CCLE_metadata.RDS ───────────────────────────────────────────────────
message("\n[4/5] CCLE_metadata.RDS ...")
meta <- readRDS(file.path(SCP542_DIR, "CCLE_metadata.RDS"))
if (is.data.frame(meta)) {
  cat("  dim:", paste(dim(meta), collapse=" x "), "\n")
  write.table(meta, file.path(OUT_DIR, "CCLE_metadata.tsv"),
              sep = "\t", row.names = FALSE, quote = TRUE)
  message("  → CCLE_metadata.tsv")
} else {
  saveRDS(meta, file.path(OUT_DIR, "CCLE_metadata.rds"))
  message("  (non-data.frame list saved as .rds)")
}

# ── 5. metaprograms_tumors_literature.txt ─────────────────────────────────
message("\n[5/5] metaprograms_tumors_literature.txt ...")
lit <- readLines(file.path(SCP542_DIR, "metaprograms_tumors_literature.txt"))
cat("  lines:", length(lit), "\n")
writeLines(lit, file.path(OUT_DIR, "metaprograms_tumors_literature.tsv"))
message("  → metaprograms_tumors_literature.tsv")

message("\n=== All conversions done ===")
