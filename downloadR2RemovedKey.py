    import boto3
    from botocore.exceptions import NoCredentialsError
    import os
    from datetime import datetime
    import re
    import shutil

    # Cloudflare R2 credentials and bucket information
    access_key = 'ADD KEY'  # Replace with your actual access key
    secret_key = 'ADD SECRET'  # Replace with your actual secret key
    bucket_name = 'asidrbackups'  # Update with your R2 bucket name
    local_directory = '/backups/'  # Local directory to save files

    # Initialize the S3 client
    s3 = boto3.client('s3', 
                    aws_access_key_id=access_key, 
                    aws_secret_access_key=secret_key, 
                    endpoint_url='https://bc341960a99d769bc26f3c0fd140b69e.r2.cloudflarestorage.com'
    )

    def setup_log_file(log_file):
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Create the log file if it doesn't exist and set permissions
        if not os.path.exists(log_file):
            open(log_file, 'a').close()
            os.chmod(log_file, 0o640)  # Read-write permissions for owner, read for group


    import boto3
    from botocore.exceptions import NoCredentialsError
    import os

    # Initialize the S3 client
    s3 = boto3.client('s3', 
                    aws_access_key_id=access_key, 
                    aws_secret_access_key=secret_key, 
                    endpoint_url='https://bc341960a99d769bc26f3c0fd140b69e.r2.cloudflarestorage.com'
    )

    def setup_log_file(log_file):
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Create the log file if it doesn't exist and set permissions
        if not os.path.exists(log_file):
            open(log_file, 'a').close()
            os.chmod(log_file, 0o640)  # Read-write permissions for owner, read for group

    def append_to_log(log_file, message):
        with open(log_file, 'a') as log:
            log.write(message + "\n")

    def delete_old_local_backups(latest_date, local_directory, log_file):
        for dir_name in os.listdir(local_directory):
            dir_path = os.path.join(local_directory, dir_name)
            if os.path.isdir(dir_path) and re.match(r'\d{4}-\d{2}-\d{2}', dir_name):
                dir_date = datetime.strptime(dir_name, '%Y-%m-%d')
                if dir_date < latest_date:
                    try:
                        shutil.rmtree(dir_path)
                        message = f"Deleted old local backup directory: {dir_path}"
                        print(message)
                        append_to_log(log_file, message)
                    except Exception as e:
                        message = f"Failed to delete {dir_path}: {e}"
                        print(message)
                        append_to_log(log_file, message)

def delete_old_remote_backups(latest_date, log_file):
    paginator = s3.get_paginator('list_objects_v2')
    delete_list = []
    for page in paginator.paginate(Bucket=bucket_name):
        for content in page.get('Contents', []):
            key = content['Key']
            # Adjusted to search for date pattern irrespective of the folder structure
            match = re.search(r'(\d{4}-\d{2}-\d{2})/', key)
            if match:
                date_str = match.group(1)
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                if date_obj < latest_date:
                    delete_list.append({'Key': key})
    # Perform deletion in batches
    if delete_list:
        try:
            response = s3.delete_objects(Bucket=bucket_name, Delete={'Objects': delete_list})
            for key in delete_list:
                message = f"Deleted old remote backup: {key['Key']}"
                print(message)
                append_to_log(log_file, message)
        except Exception as e:
            print("Error during deletion:", e)  # Log any errors during deletion
            append_to_log(log_file, f"Error during deletion: {e}")
            
    def download_files():
        log_file = '/logs/cparestore/r2.log'
        setup_log_file(log_file)

        try:
            latest_date = None
            latest_folder_prefix = None  # Holds the path structure for the latest folder

            paginator = s3.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=bucket_name):
                for content in page.get('Contents', []):
                    key = content['Key']
                    # Look for keys that have a date format in their path
                    match = re.search(r'(\d{4}-\d{2}-\d{2})/accounts/', key)
                    if match:
                        date_str = match.group(1)
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        # Compare and find the latest date
                        if not latest_date or date_obj > latest_date:
                            latest_date = date_obj
                            latest_folder_prefix = key[:match.end()]  # Up to and including 'accounts/'

            if latest_folder_prefix:
                print(f'Latest folder found: {latest_folder_prefix}')
                for obj in paginator.paginate(Bucket=bucket_name, Prefix=latest_folder_prefix):
                    for content in obj.get('Contents', []):
                        file_name = content['Key']
                        # Transform the key into the correct local path structure
                        parts = file_name.split('/')
                        local_path = os.path.join(local_directory, parts[-3], parts[-2], parts[-1])
                        
                        # Ensure the directory exists
                        os.makedirs(os.path.dirname(local_path), exist_ok=True)

                        # Download the file
                        s3.download_file(bucket_name, file_name, local_path)
                        log_message = f'Downloaded {file_name} to {local_path}\n'
                        print(log_message)
                        with open(log_file, 'a') as log:
                            log.write(log_message)

                # After downloading, delete old backups
                if latest_date:
                    delete_old_local_backups(latest_date, local_directory, log_file)
                    delete_old_remote_backups(latest_date, log_file)
            else:
                print('No matching date folders found in the bucket.')
                with open(log_file, 'a') as log:
                    log.write('No matching date folders found in the bucket.\n')

        except NoCredentialsError:
            error_message = 'Credentials not available\n'
            print(error_message)
            with open(log_file, 'a') as log:
                log.write(error_message)

    download_files()
