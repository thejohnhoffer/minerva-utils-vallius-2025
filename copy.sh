DATE="2024-12-16"

create_exhibit () {
  url_root="$1"
  identifier="$2"
  sample="$3"
  mkdir "render"

  JSON="/home/${USER}/${DATE}/json/${url_root}/${identifier}.story.json"

  RENDER_FILE="render/${url_root}__${identifier}.bash"
  cp templates/sbatch_template.sh "$RENDER_FILE"
  echo "#SBATCH --array=0-0" >> "$RENDER_FILE"
  echo "DATE=\"${DATE}\"" >> "$RENDER_FILE"
  echo "URL_ROOT=\"${url_root}\"" >> "$RENDER_FILE"
  echo "IDENTIFIER=\"${identifier}\"" >> "$RENDER_FILE"
  echo "SAMPLE=\"${sample}\"" >> "$RENDER_FILE"
  cat templates/render_template.sh >> "$RENDER_FILE"
}

create_exhibit $1 $2 $3