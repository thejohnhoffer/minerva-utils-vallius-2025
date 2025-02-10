FROM_DIR="/n/scratch/users/j/jth30/2024-12-16"
TO_DIR="/home/$USER/cycif.org/_data"
PAPER="vallius-2025"

copy_to_cycif () {
  URL_ROOT=$1
  IDENTIFIER=$2
  IN_DIR="${FROM_DIR}/${PAPER}/${URL_ROOT}/${IDENTIFIER}"
  OUT_DIR="${TO_DIR}/config-${PAPER}/${URL_ROOT}/${IDENTIFIER}"
  #echo "https://s3.amazonaws.com/www.cycif.org/${PAPER}/${URL_ROOT}/${IDENTIFIER}/index.html"
  mkdir -p "$OUT_DIR"
  cp "${IN_DIR}/exhibit.json" "${OUT_DIR}/exhibit.json"
}

copy_to_cycif $1 $2
