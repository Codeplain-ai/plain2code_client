import os
import pathlib
import shutil
import distutils.dir_util
import logging

def read_plain_source(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except IOError as e:
        raise IOError(f"Error reading The Plain Source file: {str(e)}") from e

def ensure_build_folder(build_folder):
    try:
        build_path = pathlib.Path(build_folder)
        build_path.mkdir(parents=True, exist_ok=True)
        return str(build_path.resolve())
    except Exception as e:
        raise IOError(f"Error creating or accessing The Build Folder: {str(e)}") from e

def clear_build_folder(build_folder):
    try:
        build_path = pathlib.Path(build_folder)
        if build_path.exists():
            for item in build_path.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
    except Exception as e:
        raise IOError(f"Error clearing The Build Folder: {str(e)}") from e

def copy_base_folder(base_folder, build_folder):
    try:
        if base_folder:
            distutils.dir_util.copy_tree(base_folder, build_folder)
            logging.info(f"Copied contents from The Base Folder: {base_folder} to The Build Folder: {build_folder}")
    except Exception as e:
        raise IOError(f"Error copying from The Base Folder to The Build Folder: {str(e)}") from e

def load_existing_files(build_folder):
    existing_files = {}
    try:
        for root, _, files in os.walk(build_folder):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, build_folder)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        existing_files[relative_path] = f.read()
                except Exception as e:
                    logging.warning(f"Error reading file {file_path}: {str(e)}")
        return existing_files
    except Exception as e:
        raise RuntimeError(f"Error loading existing files from {build_folder}: {str(e)}") from e

def update_build_folder(build_folder, rendered_files):
    for file_name, content in rendered_files.get('files', {}).items():
        file_path = os.path.join(build_folder, file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logging.warning(f"Error writing file {file_path}: {str(e)}")