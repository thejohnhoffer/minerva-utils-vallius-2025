DATE="2024-12-16"
mkdir "roi"

copy_roi_template () {
  url_root="$1"
  identifier="$2"
  sample="$3"
  roi_file="$4"

  JSON="/home/${USER}/${DATE}/json/${url_root}/${identifier}.story.json"

  RENDER_FILE="render/${url_root}__${identifier}.bash"
  cp templates/sbatch_template.sh "$RENDER_FILE"
  echo "#SBATCH --array=0-0" >> "$RENDER_FILE"
  echo "DATE=\"${DATE}\"" >> "$RENDER_FILE"
  echo "URL_ROOT=\"${url_root}\"" >> "$RENDER_FILE"
  echo "IDENTIFIER=\"${identifier}\"" >> "$RENDER_FILE"
  echo "SAMPLE=\"${sample}\"" >> "$RENDER_FILE"
  echo "ROI_FILE=\"${roi_file}\"" >> "$RENDER_FILE"
  cat templates/roi_template.sh >> "$RENDER_FILE"
}

copy_roi_template $1 $2 $3 $4
