#!/bin/bash

# Load variables from .env
#if [ -f .env ]; then
#  export $(grep -v '^#' .env | xargs)
#else
#  echo "Missing .env file!"
#  exit 1
#fi


# Load environment for cron
if [ -f /etc/cron.env ]; then
  set -a
  . /etc/cron.env
  set +a
fi

# this is set-up to be used by the docker image

TARGET_DIR="/app/server"
CONFIG_FILE="/app/server/server_config.yaml"

# load from server_config the urls for anycast dbs
# you search for variable "anycast_prefixes_v4_url" in the config
#URL_V4=$(grep 'anycast_prefixes_v4_url:' "$CONFIG_FILE" | sed -E 's/.*:\s*"([^"]+)"/\1/' | tr -d '\r\n')
#URL_V6=$(grep 'anycast_prefixes_v6_url:' "$CONFIG_FILE" | sed -E 's/.*:\s*"([^"]+)"/\1/' | tr -d '\r\n')
URL_V4=$(awk -F'"' '/anycast_prefixes_v4_url:/ { print $2 }' "$CONFIG_FILE" | tr -d '\r\n')
URL_V6=$(awk -F'"' '/anycast_prefixes_v6_url:/ { print $2 }' "$CONFIG_FILE" | tr -d '\r\n')

download_anycast_db() {
  FILE_NAME=$1
  URL=$2

  echo "Updating ${FILE_NAME} from ${URL}..."

  # Remove the old files
  rm -f "${TARGET_DIR}/${FILE_NAME}"

  # Download them
  STATUS_CODE=$(curl -s -o "${TARGET_DIR}/${FILE_NAME}" -w "%{http_code}" "$URL")

  if [ "$STATUS_CODE" -ne 200 ]; then
    echo "Failed to download ${FILE_NAME} (HTTP $STATUS_CODE)"
    exit 1
  fi

  echo "${FILE_NAME} updated successfully"
}

download_and_extract() {
  DB_NAME=$1
  TARGET_FILE="${TARGET_DIR}/${DB_NAME}.mmdb"
  if [ -f "$TARGET_FILE" ]; then
    if find "$TARGET_FILE" -mmin -1380 | grep -q .; then
      echo "${DB_NAME}.mmdb is less than 24 hours old. Skipping download."
      return 0
    else
      echo "${DB_NAME}.mmdb is older than 24 hours. Updating..."
    fi
  else
    echo "${DB_NAME}.mmdb does not exist. Downloading..."
  fi

  echo "Downloading ${DB_NAME}..."
  curl -O -J -L -u "$ACCOUNT_ID:$LICENSE_KEY" "https://download.maxmind.com/geoip/databases/${DB_NAME}/download?suffix=tar.gz"

  echo "Extracting ${DB_NAME}..."
  tar -xzf ${DB_NAME}_*.tar.gz

  EXTRACTED_DIR=$(tar -tzf ${DB_NAME}_*.tar.gz | head -1 | cut -f1 -d"/")
  MMDB_FILE=$(find "$EXTRACTED_DIR" -name "*.mmdb" | head -n 1)

  if [ -z "$MMDB_FILE" ]; then
    echo "Error: .mmdb file not found for ${DB_NAME}."
    return 1
  fi

  echo "Moving .mmdb to ${TARGET_DIR}/${DB_NAME}.mmdb"
  mv "$MMDB_FILE" "${TARGET_DIR}/${DB_NAME}.mmdb"

  echo "Cleaning up..."
  rm ${DB_NAME}_*.tar.gz
  rm -r "$EXTRACTED_DIR"

  echo "${DB_NAME}.mmdb update complete!"
  touch "${TARGET_DIR}/${DB_NAME}.mmdb"
}

download_anycast_db "anycast-v4-prefixes.txt" "$URL_V4"
download_anycast_db "anycast-v6-prefixes.txt" "$URL_V6"
echo "All anycast prefix files are up to date."

download_and_extract "GeoLite2-City"
download_and_extract "GeoLite2-Country"
download_and_extract "GeoLite2-ASN"

echo "All db files are up to date."