
module load miniconda3
eval "$(conda shell.bash hook)"
conda activate minerva-author
which python

BUCKET="www.cycif.org"
PAPER="vallius-2025"
SCRATCH="/n/scratch/users/${USER:0:1}/${USER}"
SCRIPT="/home/${USER}/minerva-author/src/render.py --force --threads 4"

create_story () {
  url_root="$1"
  identifier="$2"
  sample="$3"
  OUT_DIR="${SCRATCH}/${DATE}/${PAPER}/${url_root}/${identifier}"
  IMG="${SCRATCH}/${DATE}/tif/${url_root}/${identifier}/${sample}.ome.tif"
  URL="https://s3.amazonaws.com/${BUCKET}/${PAPER}/${url_root}/${identifier}"
  JSON="/home/${USER}/${DATE}/json/${url_root}/${identifier}.story.json"

  # Without masks available
  python $SCRIPT "$IMG" "$JSON" "$OUT_DIR" --url "$URL"
}

create_story "${URL_ROOT}" "${IDENTIFIER}" "${SAMPLE}"
