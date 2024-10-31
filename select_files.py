#!/usr/bin/env python3

import os
import sys
import fnmatch
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
import readchar
import pyperclip
import argparse
from rich.style import Style

def load_ignore_patterns(ignore_files):
    """Load ignore patterns from a list of files."""
    patterns = []
    for ignore_file in ignore_files:
        if os.path.exists(ignore_file):
            with open(ignore_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)
    return patterns

def is_ignored(path, patterns, root_dir):
    """Check if the path matches any of the ignore patterns."""
    relative_path = os.path.relpath(path, root_dir)
    path_parts = relative_path.split(os.sep)

    for pattern in patterns:
        if pattern.endswith('/'):
            # Directory pattern
            dir_pattern = pattern.rstrip('/')
            if dir_pattern in path_parts:
                return True
        else:
            # File pattern with possible wildcards
            if fnmatch.fnmatch(os.path.basename(path), pattern):
                return True
    return False

def list_files(root_dir, ignore_files):
    """List files in root_dir, ignoring patterns from specified ignore files."""
    ignore_patterns = load_ignore_patterns(ignore_files)

    files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Filter directories in-place
        dirnames[:] = [d for d in dirnames if not is_ignored(os.path.join(dirpath, d), ignore_patterns, root_dir)]

        # Filter and add files
        for file in filenames:
            file_abs_path = os.path.join(dirpath, file)
            if not is_ignored(file_abs_path, ignore_patterns, root_dir):
                files.append(file_abs_path)
    return files

def get_file_color(file_path):
    """Determine the color for the file path based on its type."""
    if os.path.isdir(file_path):
        return "blue"
    elif file_path.endswith('.py'):
        return "white"
    else:
        # Generate a shade of grey based on the file extension
        ext = os.path.splitext(file_path)[1]
        hash_value = hash(ext) % 200  # Using modulo to limit the range
        return f"rgb({hash_value},{hash_value},{hash_value})"

def get_folder_colors():
    """Return a list of 16 distinct, readable colors for use on a black background."""
    return [
        "bright_red", "bright_green", "bright_yellow", "bright_blue",
        "bright_magenta", "bright_cyan", "bright_white", "orange1",
        "deep_sky_blue1", "spring_green1", "gold1", "deep_pink1",
        "light_sea_green", "purple", "khaki1", "medium_violet_red"
    ]

def assign_folder_colors(files):
    """Assign colors to folders based on their names."""
    folders = set(os.path.dirname(file) for file in files)
    colors = get_folder_colors()
    return {folder: colors[i % len(colors)] for i, folder in enumerate(folders)}

def display_files(files, selected, key_mapping):
    """Display files with their assigned keys, selection status, and color-coded folders."""
    console = Console()
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("S", width=1)
    table.add_column("Key", width=1)
    table.add_column("Filename", style="cyan")
    table.add_column("Folder", style="green")
    table.add_column("Extension", style="yellow")

    folder_colors = assign_folder_colors(files)

    for idx, file in enumerate(files):
        key = key_mapping.get(idx, '?')
        selected_mark = '[green]✔️[/green]' if idx in selected else ''
        
        filename = os.path.basename(file)
        name, ext = os.path.splitext(filename)
        folder = os.path.dirname(file)
        folder_name = os.path.basename(folder)
        
        file_color = folder_colors[folder]
        name_style = Style(color=file_color)
        
        # Update this line to use the style correctly
        table.add_row(
            selected_mark,
            key,
            f"[{file_color}]{name}[/{file_color}]",  # Apply the style directly in the string
            folder_name,
            ext
        )

    console.clear()
    console.print(table)

def assign_keys(num_files, key_sequence):
    """Assign unique keys from a predefined sequence to each file."""
    if num_files > len(key_sequence):
        print(f"Too many files! Showing only the first {len(key_sequence)} files.")
        return {idx: key_sequence[idx] for idx in range(len(key_sequence))}, True
    return {idx: key_sequence[idx] for idx in range(num_files)}, False

def get_key_mapping(keys):
    """Reverse mapping from key to index."""
    return {v: k for k, v in keys.items()}

def concatenate_selected_files(selected, files, root_dir):
    """Concatenate content of selected files and tree.txt into a single output file and copy to clipboard."""
    output_content = ""
    output_file = os.path.join(root_dir, 'concatenated_output.txt')

    with open(output_file, 'w') as outfile:
        # Include tree.txt if it exists
        tree_file = os.path.join(root_dir, 'tree.txt')
        if os.path.exists(tree_file):
            with open(tree_file, 'r') as tf:
                tree_content = tf.read()
                output_content += f"# {tree_file}\n{tree_content}\n"
                outfile.write(f"# {tree_file}\n{tree_content}\n")
        else:
            print(f"Warning: {tree_file} does not exist and will not be included.")

        # Append selected files
        for idx in selected:
            file_path = files[idx]
            try:
                with open(file_path, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    output_content += f"# {file_path}\n{content}\n"
                    outfile.write(f"# {file_path}\n{content}\n")
            except FileNotFoundError:
                print(f"Warning: Could not find file {file_path}. Skipping.")
            except UnicodeDecodeError:
                print(f"Warning: Could not decode file {file_path}. Skipping.")
            except Exception as e:
                print(f"Warning: Could not read file {file_path}. Error: {e}. Skipping.")

    # Copy the concatenated content to the clipboard
    try:
        pyperclip.copy(output_content)
        print(f"Files concatenated into {output_file} and copied to clipboard.")
    except pyperclip.PyperclipException:
        print(f"Files concatenated into {output_file}. Failed to copy to clipboard.")

def interactive_file_selection(files, key_mapping, root_dir):
    """Interactively select files using the assigned keys."""
    selected = set()
    key_to_index = get_key_mapping(key_mapping)

    while True:
        display_files(files, selected, key_mapping)
        key = readchar.readkey()
        if key == '\n':  # Save and exit on Enter key
            break
        elif key in key_to_index:
            idx = key_to_index[key]
            if idx in selected:
                selected.remove(idx)
            else:
                selected.add(idx)
        # Ignore other keys
    return selected

def main():
    parser = argparse.ArgumentParser(description="Select files from a directory.")
    parser.add_argument("directory", help="The directory to select files from.")
    args = parser.parse_args()

    root_dir = args.directory
    if not os.path.isdir(root_dir):
        print(f"Error: {root_dir} is not a directory.")
        sys.exit(1)

    # Define ignore files: .gitignore and .selectignore
    gitignore = os.path.join(root_dir, '.gitignore')
    selectignore = os.path.join(root_dir, '.selectignore')
    ignore_files = [gitignore, selectignore]

    files = list_files(root_dir, ignore_files)
    if not files:
        print("No files to select.")
        sys.exit(0)

    # Predefined key sequence
    key_sequence = list("aAbBcCdDeEfFgGhHiIjJkKlLmMnNoOpPqQrRsStT1234567890!@#$%^&*()")
    key_mapping, paging_required = assign_keys(len(files), key_sequence)
    if paging_required:
        print("Paging required due to too many files. Consider refining your ignore patterns.")
    
    selected = interactive_file_selection(files, key_mapping, root_dir)

    # Display selected files
    print("\nSelected Files:")
    for idx in selected:
        print(f"- {files[idx]}")

    # Concatenate selected files and tree.txt
    concatenate_selected_files(selected, files, root_dir)

if __name__ == "__main__":
    main()
