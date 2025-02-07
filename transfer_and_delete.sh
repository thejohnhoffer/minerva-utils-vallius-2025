DATE="2024-12-16"
BUCKET="www.cycif.org"
PAPER="vallius-2025"
SCRATCH="/n/scratch/users/${USER:0:1}/${USER}"

transfer_story () {
  URL="s3://${BUCKET}/${PAPER}"
  DIR="${SCRATCH}/${DATE}/${PAPER}"
  CMD="s3 sync --acl public-read --storage-class INTELLIGENT_TIERING $DIR $URL"
  echo "aws $CMD"
  aws $CMD
  # Prompt the user before removing!
  rm -r $DIR
}

transfer_story
