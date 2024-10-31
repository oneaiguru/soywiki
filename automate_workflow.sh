#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

PROJECT_DIR="/Users/m/git/lubot"

# Check if the project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Error: Directory $PROJECT_DIR does not exist."
    exit 1
fi

# Generate tree.txt
echo "Generating tree.txt..."
python folder_structure_generator.py "$PROJECT_DIR" --output "$PROJECT_DIR/tree.txt"

# Check if tree.txt was created
if [ ! -f "$PROJECT_DIR/tree.txt" ]; then
    echo "Error: Failed to create tree.txt."
    exit 1
fi

echo "tree.txt generated successfully."

# Select and concatenate files
echo "Launching select_files.py for interactive file selection..."
python select_files.py "$PROJECT_DIR"

echo "Process completed successfully."
