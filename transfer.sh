DATE="2024-12-16"
BUCKET="www.cycif.org"
PAPER="vallius-2025"
SCRATCH="/n/scratch/users/${USER:0:1}/${USER}"

transfer_story () {
  url_root=$1
  identifier=$2
  URL="s3://${BUCKET}/${PAPER}/${url_root}/${identifier}"
  DIR="${SCRATCH}/${DATE}/${PAPER}/${url_root}/${identifier}"
  CMD="s3 sync --acl public-read --storage-class INTELLIGENT_TIERING $DIR $URL"
  echo "aws $CMD"
  aws $CMD
}

transfer_story $1 $2
