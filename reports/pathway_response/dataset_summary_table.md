# Extended Data Fig. 1 — Dataset Summary

## Primary experimental data (this study)

| Dataset | Cell line | Size (genes x cells) | Perturbations | Control cells | Perturbation type |
|---------|-----------|---------------------|---------------|---------------|-------------------|
| GSE241115 | HCC38 (breast cancer) | 36,601 x 14,175 | 47 | 1,666 | CRISPRi |
| GSE241115 | HCC1143 (breast cancer) | 36,601 x 11,405 | 47 | 1,325 | CRISPRi |

## Supplementary experimental data

| Dataset | Cell line | Size (genes x cells) | Perturbations | Control cells | Perturbation type |
|---------|-----------|---------------------|---------------|---------------|-------------------|
| GSE90063 | K562 (7d) | 23,111 x 28,034 | 10 | 5,381 | CRISPRi TF |
| GSE90063 | K562 (13d) | 21,713 x 15,849 | 10 | 3,491 | CRISPRi TF |
| GSE90063 | K562 (control-context) | 23,712 x 30,486 | 248 | 3,770 | CRISPRi |

## External benchmark data (model training / Stage 1a)

| Dataset | Cell line | Size (genes x cells) | Perturbations | Source |
|---------|-----------|---------------------|---------------|--------|
| Replogle et al., 2022 | K562 (essential) | 8,563 x 310,385 | 2,057 single | [^1] |
| Replogle et al., 2022 | RPE1 | 8,749 x 247,914 | 1,534 single | [^1] |
| Tian et al., 2019 | iPSC | 33,752 x 275,708 | ~100 single | [^2] |
| Tian et al., 2019 | Neuron (day 7) | 33,752 x 182,790 | ~100 single | [^2] |
| Tian et al., 2021 | K562 (CRISPRi) | 33,538 x 32,300 | 81 single | [^3] |
| Norman et al., 2019 | K562 | 33,694 x 111,445 | 124 double + 100 single | [^4] |

## External endpoint data

| Dataset | Description | Coverage | Source |
|---------|-------------|----------|--------|
| DepMap CRISPR | Gene effect + gene dependency | 700+ cell lines | DepMap Portal |
| DEMETER2 | RNAi gene dependency (converted) | 701 cell lines x 17,309 genes | [^5] |

---

**References**

[^1]: Replogle et al. (2022). *Nature Genetics* 54, 1577–1589.
[^2]: Tian et al. (2019). *Nature Methods* 16, 1167–1176.
[^3]: Tian et al. (2021). *Nature Biotechnology* 39, 719–728.
[^4]: Norman et al. (2019). *Science* 366, 786–793.
[^5]: Tsherniak et al. (2017). *Nature Genetics* 49, 1779–1784.
