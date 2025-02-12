FROM_DIR="/n/scratch/users/j/jth30/2024-12-16"
TO_DIR1="/home/$USER/cycif.org/_data"
TO_DIR2="/home/$USER/cycif.org/data"
PAPER="vallius-2025"

copy_to_cycif () {
  URL_ROOT=$1
  IDENTIFIER=$2
  IN_DIR="${FROM_DIR}/${PAPER}/${URL_ROOT}/${IDENTIFIER}"
  OUT_DIR1="${TO_DIR1}/config-${PAPER}/${URL_ROOT}/${IDENTIFIER}"
  OUT_DIR2="${TO_DIR2}/${PAPER}/${URL_ROOT}/${IDENTIFIER}"

  mkdir -p "$OUT_DIR1"
  mkdir -p "$OUT_DIR2"

  cp "${IN_DIR}/exhibit.json" "${OUT_DIR1}/exhibit.json"

  echo "---" > "${OUT_DIR2}/index.md" 
  echo "title: ${IDENTIFIER}" >> "${OUT_DIR2}/index.md" 
  echo "layout: minerva-1-5" >> "${OUT_DIR2}/index.md" 
  echo "exhibit: config-${PAPER}/${URL_ROOT}/${IDENTIFIER}" >> "${OUT_DIR2}/index.md"
  echo "images: https://s3.amazonaws.com/www.cycif.org/${PAPER}/${URL_ROOT}/${IDENTIFIER}" >> "${OUT_DIR2}/index.md"
  echo "---" >> "${OUT_DIR2}/index.md" 
}

copy_to_cycif $1 $2
