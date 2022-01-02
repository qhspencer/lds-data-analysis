#!/bin/bash

# This is the export command I'm using to convert the content of the notebooks directory
# to markdown documents to be published via GitHub pages.
#NOTEBOOKS_DIR=notebooks
SITE_DIR=docs
INPUT_FILE=$1
NAME=$(basename ${INPUT_FILE/\ /-})
OUTPUT_FILE=$(date -r "$INPUT_FILE" +%Y-%m-%d-)${NAME//.*}
echo "input file:  "$INPUT_FILE
echo "output file: "$OUTPUT_FILE

jupyter jekyllnb "$INPUT_FILE" \
	 --site-dir docs \
	 --page-dir _posts \
	 --image-dir assets/images \
	 --output $OUTPUT_FILE \
	 --no-input \
	 -TagRemovePreprocessor.remove_cell_tags javascript
