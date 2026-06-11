#!/bin/bash
set -e
SERIES_DIR="/home/data/gz0705/WTKO/data/raw/gse264667/series"
EXPECTED_JURKAT=9366490264
EXPECTED_HEPG2=5614460941

echo "=== GSE264667 Download Monitor ==="
echo "Started at: $(date)"

while true; do
    JURKAT_SIZE=$(stat -c%s "$SERIES_DIR/GSE264667_jurkat_raw_singlecell_01.h5ad" 2>/dev/null || echo 0)
    HEPG2_SIZE=$(stat -c%s "$SERIES_DIR/GSE264667_hepg2_raw_singlecell_01.h5ad" 2>/dev/null || echo 0)

    JURKAT_PCT=$(echo "scale=1; $JURKAT_SIZE * 100 / $EXPECTED_JURKAT" | bc 2>/dev/null || echo 0)
    HEPG2_PCT=$(echo "scale=1; $HEPG2_SIZE * 100 / $EXPECTED_HEPG2" | bc 2>/dev/null || echo 0)

    echo "$(date) | jurkat: ${JURKAT_SIZE}/${EXPECTED_JURKAT} (${JURKAT_PCT}%) | hepg2: ${HEPG2_SIZE}/${EXPECTED_HEPG2} (${HEPG2_PCT}%)"

    if [ "$JURKAT_SIZE" -ge "$EXPECTED_JURKAT" ] && [ "$HEPG2_SIZE" -ge "$EXPECTED_HEPG2" ]; then
        echo ""
        echo "=== BOTH FILES COMPLETE ==="
        echo "Verifying jurkat..."
        python3 /home/data/gz0705/WTKO/scripts/download/verify_h5ad.py "$SERIES_DIR/GSE264667_jurkat_raw_singlecell_01.h5ad" || true
        echo ""
        echo "Verifying hepg2..."
        python3 /home/data/gz0705/WTKO/scripts/download/verify_h5ad.py "$SERIES_DIR/GSE264667_hepg2_raw_singlecell_01.h5ad" || true
        echo "=== DONE at $(date) ==="
        break
    fi

    sleep 60
done
