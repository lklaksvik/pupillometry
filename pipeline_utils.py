# tools to facilitate eyebrain_pipeline

# import libraries
import os
from pathlib import Path
from datetime import datetime

def create_subject_folder(subject_id):
    """
    Creates a folder on the desktop with user confirmation if it already exists.
    Works on both Windows and macOS/Linux.
    
    Args:
        subject_id (str): subejct ID to create a folder for.
    
    Returns:
        subject_dir (Path): Path object pointing to the subject directory.
    """

    # define path to the subject directory
    datestamp = datetime.now().strftime('%Y%m%d')
    home_path = Path.home()
    desktop_path = home_path / 'Desktop'
    folder_name = f'sub-{subject_id}_ses-01_dat-{datestamp}'
    folder_path = desktop_path / folder_name

    # Check if folder already exists and prompt user for confirmation
    if folder_path.exists():
        print(f"Warning: Folder '{folder_name}' already exists at: {folder_path}")
        response = input("Do you want to proceed anyway? (y/n): ").lower().strip()
        
        if response not in ['y', 'yes']:
            print("Operation cancelled.")
            return False

    # Create folder (this will overwrite any existing folders)
    print("Proceeding with creating folder...")
    try:
        folder_path.mkdir(exist_ok=True)
        print(f"Folder '{folder_name}' created successfully at: {folder_path}")
        return folder_path
    except Exception as e:
        print(f"Error creating folder: {e}")
        return False            
            