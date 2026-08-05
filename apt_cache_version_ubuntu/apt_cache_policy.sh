#!/bin/bash
# Author - Gururaj Rao

# Check if any arguments were provided
if [ "$#" -eq 0 ]; then
    echo "Usage: $0 apt-package.lst" 
    exit 1
fi
PACKAGE_LINE_CONTENT=$(tr '\n' ' ' < apt-package.lst)
echo "$PACKAGE_LINE_CONTENT"
set -- ${PACKAGE_LINE_CONTENT}
# Loop through all arguments provided to the script
for package in "$@"; do
    echo "------------------------------------"
    echo "Checking version for: $package"

    # Check if the package exists in the APT cache
    if apt-cache show "$package" &>/dev/null; then
        # Package exists, so get its policy
        apt-cache policy "$package"|tee -a guru_apt-cache.out
    else
        # Package does not exist
        echo "Error: Package '$package' not found."
    fi
    echo "------------------------------------"
    echo "" # Add a blank line for readability
done
