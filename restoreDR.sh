#!/bin/bash

# Path to the download script
download_script="/scripts/DR/downloadR2.py"  # Update with the actual path

# Running the download script
echo "Starting the download of files..."
python3 "$download_script"
echo "Download complete."


# Log file location
log_dir="/logs/cparestore"
log_file="$log_dir/restore.log"

# Check if log directory exists, if not create it
if [ ! -d "$log_dir" ]; then
    echo "Creating log directory $log_dir..."
    sudo mkdir -p "$log_dir"
    sudo chmod 755 "$log_dir"
    # Set the ownership to the user running the script. Replace 'your_username' with the actual username.
    # sudo chown your_username:your_username "$log_dir"
fi

# Base backup directory
base_backup_dir="/backups/"

# Find the latest backup directory based on folder name with date format YYYY-MM-DD
latest_backup_dir=$(find "$base_backup_dir" -maxdepth 1 -type d -name '????-??-??' | xargs -I {} basename {} | sort -r | head -n 1)
latest_backup_dir="$base_backup_dir$latest_backup_dir"

# Directory paths
account_backup_dir="$latest_backup_dir/accounts"

# Logging start
echo "Restoration process started at $(date)" | tee -a "$log_file"

# Restore cPanel accounts
echo "Restoring cPanel accounts..." | tee -a "$log_file"
for backup_file in "$account_backup_dir"/*.tar.gz; do
    if [ -f "$backup_file" ]; then
        account_name=$(basename "$backup_file" .tar.gz)
        echo "Restoring account $account_name..." | tee -a "$log_file"

        # Delete account if it exists
        echo "Deleting account $account_name if exists..." | tee -a "$log_file"
        /usr/local/cpanel/scripts/removeacct --force $account_name

        # Restore account from backup
        echo "Restoring $(basename "$backup_file")..." | tee -a "$log_file"
        /usr/local/cpanel/scripts/restorepkg "$backup_file" 2>&1 | tee -a "$log_file"

        # Fix permissions for each account
        echo "Fixing permissions for $account_name..." | tee -a "$log_file"
        find /home/$account_name/public_html/ -type f -exec chmod 644 {} \;
        find /home/$account_name/public_html/ -type d -exec chmod 755 {} \;
        echo "Permissions fixed for $account_name." | tee -a "$log_file"
    fi
done

echo "Restoration process completed at $(date)" | tee -a "$log_file"

