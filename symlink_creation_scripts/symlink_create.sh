#!/bin/bash

# This script creates RELATIVE symbolic links from files in a source SYSTEM_BUILD used for Android 14 split build structure
# to a specified destination directory (VENDOR_BUILD), maintaining the original directory structure (depth/level).
# It ensures that only symbolic links are created, not hard links or copies.

#Contact: Gururaj Rao

# Function to display usage information
usage() {
    echo "Usage: $0 <source_directory> <destination_directory>"
    echo "  <source_directory>: The directory containing the original files and subdirectories viz. SYSTEM_BUILD directory contents."
    echo "  <destination_directory>: The directory where relative symbolic links will be created, with preserved structure of SYSTEM_BUILD in VENDOR_BUILD contents."
    echo "Example ./symlinks_create.sh SYSTEM_BUILD VENDOR_BUILD, since SYSTEM_BUILD and VENDOR_BUILD located in the <ROOT_WORKSPACE>"
    exit 1
}

# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
    usage
fi

SOURCE_DIR="$1"
DEST_DIR="$2"

# Ensure SOURCE_DIR ends with a trailing slash for easier path manipulation
# Remove trailing slash if exists, then add it back
SOURCE_DIR=$(echo "$SOURCE_DIR" | sed 's/\/*$//') 
SOURCE_DIR="$SOURCE_DIR/" 

# Ensure DEST_DIR ends with a trailing slash for easier path manipulation
# Remove trailing slash if exists, then add it back
DEST_DIR=$(echo "$DEST_DIR" | sed 's/\/*$//') 
DEST_DIR="$DEST_DIR/"

# Check if the source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory '$SOURCE_DIR' does not exist."
    exit 1
fi

# Create the destination directory if it doesn't exist
# The -p flag creates parent directories if they don't exist
if [ ! -d "$DEST_DIR" ]; then
    echo "Destination directory '$DEST_DIR' does not exist. Creating it..."
    mkdir -p "$DEST_DIR"
    if [ $? -ne 0 ]; then
        echo "Error: Could not create destination directory '$DEST_DIR'."
        exit 1
    fi
fi

echo "Creating RELATIVE symbolic links from '$SOURCE_DIR' to '$DEST_DIR' maintaining directory depth..."

# Function to calculate relative path from one absolute path to another
# Usage: get_relative_path <from_path> <to_path>
get_relative_path() {
    local from_path="$1"
    local to_path="$2"

    # Use python to calculate the relative path, as it's more robust than pure bash for complex paths
    #python3 -c "import os.path; print(os.path.relpath('$to_path', '$from_path'))"


    # Get the absolute paths first
    abs_to_path=$(realpath "$to_path")
    abs_from_path=$(realpath "$from_path")

    # Find the common prefix basically upto HOME Directory
    common_prefix=$(printf "%s\n%s\n" "$abs_from_path" "$abs_to_path" | sed -e 'N;s/^\(.*\).*\n\1.*$/\1/;t' -e 's/\(.*\)\/.*/\1/')

    # Remove the common prefix from both paths
    relative_to_from="${abs_from_path#$common_prefix}"
    relative_to_to="${abs_to_path#$common_prefix}"

    # Count directories in from_path to determine how many "../" are needed
    num_dirs=$(echo "$relative_to_from" | tr -cd '/' | wc -c)

    # Construct the relative path starting from SYSTEM_BUILD
    relative_path="../" # Since SYSTEM_BUILD and VENDOR_BUILD lies in the same root structure
    for i in $(seq 1 $num_dirs); do
       relative_path+="../"
    done

    relative_path+="${relative_to_to#\/}" # Remove leading slash if any
    echo "$relative_path"
}


# Loop through each item in the source directory (recursively)
# -type f ensures we only process regular files
find "$SOURCE_DIR" -type f -print0 | while IFS= read -r -d $'\0' file; do
    # Get the path relative to the SOURCE_DIR
    relative_source_path="${file#$SOURCE_DIR}"
    
    # Define the full path for the symbolic link in the destination directory
    symlink_path="$DEST_DIR$relative_source_path"
    
    # Get the directory where the symbolic link will be created
    symlink_dir=$(dirname "$symlink_path")

    # Create the necessary subdirectories in the destination if they don't exist
    if [ ! -d "$symlink_dir" ]; then
        mkdir -p "$symlink_dir"
        if [ $? -ne 0 ]; then
            echo "Error: Could not create directory '$symlink_dir'. Skipping symlink for '$file'."
            continue # Skip to the next file
        fi
    fi

    # Check if a file or link with the same name already exists in the destination
    if [ -e "$symlink_path" ]; then
        echo "Warning: Link or file '$symlink_path' already exists. Skipping."
    else
        if [[ "$symlink_path" =~ "out" ]] || [[ "$symlink_path" =~ "system_prebuilt_dir" ]] || [[ "$symlink_path" =~ "vendor/qcom/proprietary" ]]; then
          continue # To skip out, system_prebuilt_dir and vendor/qcom/proprietary
           if [[ "$symlink_path" =~ ".mk" ]] || [[ "$symlink_path" =~ ".bp" ]] || [[ "$symlink_path" =~ "build" ]]; then
               cp -f "$symlink_path" "$relative_target"  #Copying needed for few paths
           fi
        fi

        # Calculate the relative target path from the symlink's directory to the original file
        relative_target=$(get_relative_path "$symlink_dir" "$(realpath "$file")")
        
        # Create the symbolic link using the relative target using force to create symlinks
        # ln -fs <relative_target> <link_directory_path>
        ln -s "$relative_target" "$symlink_path"  #To preserve symlinks and relative tag for VENDOR_BUILD
        
        # Check if the symbolic link creation was successful
        if [ $? -eq 0 ]; then
            echo "Successfully created RELATIVE symlink: $symlink_path -> $relative_target (points to $(realpath "$file"))"
        else
            echo "Error: Failed to create relative symlink for '$file'."
        fi
    fi
done

echo "Relative symbolic link creation process from $SOURCE_DIR to $DEST_DIR completed."



