import os
import sys
import pathlib
import shutil
import logging

logger = logging.getLogger(__name__)

def create_build_folder(build_folder):
    """Create the build folder if it doesn't exist."""
    try:
        pathlib.Path(build_folder).mkdir(parents=True, exist_ok=True)
        logger.info(f"Build folder created or already exists: {build_folder}")
    except Exception as e:
        logger.error(f"Failed to create build folder: {str(e)}")
        sys.exit(1)

def clear_build_folder(build_folder):
    """Clear the build folder of all files and subdirectories."""
    try:
        if os.path.exists(build_folder):
            for item in os.listdir(build_folder):
                item_path = os.path.join(build_folder, item)
                if os.path.isfile(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            logger.info(f"Build folder cleared: {build_folder}")
        create_build_folder(build_folder)
    except Exception as e:
        logger.error(f"Failed to clear build folder: {str(e)}")
        sys.exit(1)

def copy_base_files(base_folder, build_folder):
    """Copy files from The Base Folder to The Build Folder."""
    try:
        if os.path.exists(base_folder):
            for item in os.listdir(base_folder):
                src = os.path.join(base_folder, item)
                dst = os.path.join(build_folder, item)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                elif os.path.isdir(src):
                    shutil.copytree(src, dst)
            logger.info(f"Files copied from {base_folder} to {build_folder}")
    except Exception as e:
        logger.error(f"Failed to copy files from base folder: {str(e)}")

def load_existing_files(build_folder):
    """Load all existing files in The Build Folder."""
    existing_files = {}
    try:
        for root, _, files in os.walk(build_folder):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, build_folder)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    existing_files[relative_path] = content
                except Exception as e:
                    logger.warning(f"Failed to read file {file_path}: {str(e)}")
        return existing_files
    except Exception as e:
        logger.error(f"Failed to load existing files: {str(e)}")
        return {}

def write_rendered_files(build_folder, rendered_files):
    """Write the rendered files to the build folder."""
    for file in rendered_files:
        file_path = os.path.join(build_folder, file)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(rendered_files[file])
            logger.info(f"Written rendered file: {file}")
        except IOError as e:
            logger.error(f"Error writing rendered file {file['file_name']}: {str(e)}")