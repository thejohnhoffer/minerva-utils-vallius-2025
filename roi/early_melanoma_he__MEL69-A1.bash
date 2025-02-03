#!/bin/bash
#SBATCH -c 4
#SBATCH -p short
#SBATCH --mem 4g
#SBATCH -e slurm-%A_%a.err
#SBATCH -o slurm-%A_%a.out
#SBATCH -t 4:00:00
#SBATCH --array=0-0
DATE="2024-12-16"
URL_ROOT="early_melanoma_he"
IDENTIFIER="MEL69-A1"
SAMPLE="LSP11783"
ROI_FILE="/n/files/HiTS/lsp-analysis/cycif-production/16-Pre-Cancer-Atlas-for-Melanoma/minerva_stories2024/HE_roi_coordinates/LSP11783.ome.tif-1581122-rois.csv"

module load miniconda3
eval "$(conda shell.bash hook)"
conda activate deform
which python

BUCKET="www.cycif.org"
PAPER="vallius-2025"
SCRATCH="/n/scratch/users/${USER:0:1}/${USER}"
SCRIPT="/home/${USER}/deform-registration-stic/04-2-make-roi-svg.py run"

create_roi_tiff () {
  url_root="$1"
  identifier="$2"
  sample="$3"
  roi_file="$4"
  OUT_DIR="${SCRATCH}/${DATE}/${PAPER}/${url_root}/${identifier}"
  IMG="${SCRATCH}/${DATE}/tif/${url_root}/${identifier}/${sample}.ome.tif"

  # TODO remove preview flag
  python $SCRIPT --preview --out-dir="${OUT_DIR}" --img-path="${IMG}" --roi-path="${roi_file}"
  #python $SCRIPT --out-dir="${OUT_DIR}" --img-path="${IMG}" --roi-path="${roi_file}"
}

create_roi_tiff "${URL_ROOT}" "${IDENTIFIER}" "${SAMPLE}" "${ROI_FILE}"
