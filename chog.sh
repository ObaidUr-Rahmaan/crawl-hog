#!/bin/bash

if [ "$#" -lt 2 ]; then
    echo "Usage: ./chog.sh <url-to-scrape> <output-folder> [--single]"
    exit 1
fi

URL=$1
OUTPUT_DIR=$2
SINGLE_FLAG=""

# Check for --single flag
if [ "$3" = "--single" ]; then
    SINGLE_FLAG="--single"
fi

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Run the Python script and move results
python crawl.py "$URL" $SINGLE_FLAG

# Get the domain from the URL for the source folder name
DOMAIN=$(echo "$URL" | awk -F[/:] '{print $4}')
SOURCE_DIR="${DOMAIN}-docs"

# Move contents to specified output directory
if [ -d "$SOURCE_DIR" ]; then
    mv "$SOURCE_DIR"/* "$OUTPUT_DIR/"
    rmdir "$SOURCE_DIR"
    echo "Documentation saved to $OUTPUT_DIR"
else
    echo "Error: Crawl failed or no documentation was generated"
    exit 1
fi 