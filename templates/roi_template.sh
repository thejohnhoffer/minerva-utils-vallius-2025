
module load miniconda3
eval "$(conda shell.bash hook)"
conda activate render-roi
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

  python $SCRIPT --out-dir="${OUT_DIR}" --img-path="${IMG}" --roi-path="${roi_file}"
}

create_roi_tiff "${URL_ROOT}" "${IDENTIFIER}" "${SAMPLE}" "${ROI_FILE}"
