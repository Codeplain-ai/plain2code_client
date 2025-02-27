import os

import difflib

from liquid import Environment, FileSystemLoader, StrictUndefined
from liquid.exceptions import UndefinedError

BINARY_FILE_EXTENSIONS = ['.pyc']


def list_all_text_files(directory):
    all_files = []
    for root, dirs, files in os.walk(directory, topdown=False):
        modified_root = os.path.relpath(root, directory)
        if modified_root == '.':
            modified_root = ''

        for filename in files:
            if not any(filename.endswith(ending) for ending in BINARY_FILE_EXTENSIONS):
                try:
                    with open(os.path.join(root, filename), 'rb') as f:
                        f.read().decode('utf-8')
                except UnicodeDecodeError:
                    print(f"WARNING! Not listing {filename} in {root}. File is not a text file. Skipping it.")
                    continue

                all_files.append(os.path.join(modified_root, filename))
    
    return all_files


def list_folders_in_directory(directory):
    # List all items in the directory
    items = os.listdir(directory)
    
    # Filter out the folders
    folders = [item for item in items if os.path.isdir(os.path.join(directory, item))]
    
    return folders


def delete_files_and_subfolders(directory, verbose=False):
    total_files_deleted = 0
    total_folders_deleted = 0
    items_deleted = []
    
    # Walk the directory in reverse order (bottom-up)
    for root, dirs, files in os.walk(directory, topdown=False):
        # Delete files
        for file in files:
            file_path = os.path.join(root, file)
            os.remove(file_path)
            total_files_deleted += 1
            if verbose and len(items_deleted) < 10:
                items_deleted.append(f"Deleted file: {file_path}")
        
        # Delete directories
        for dir_ in dirs:
            dir_path = os.path.join(root, dir_)
            os.rmdir(dir_path)
            total_folders_deleted += 1
            if verbose and len(items_deleted) < 10:
                items_deleted.append(f"Deleted folder: {dir_path}")
    
    # Print the results
    if verbose:
        if total_files_deleted + total_folders_deleted > 10:
            print(f"Total files deleted: {total_files_deleted}")
            print(f"Total folders deleted: {total_folders_deleted}")
        else:
            for item in items_deleted:
                print(item)


def copy_file(source_path, destination_path):
    # Ensure the destination directory exists
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)

    # Open the source file in read-binary ('rb') mode
    with open(source_path, 'rb') as source_file:
        # Open the destination file in write-binary ('wb') mode
        with open(destination_path, 'wb') as destination_file:
            # Copy the content from source to destination
            while True:
                # Read a chunk of the source file
                chunk = source_file.read(4096)  # Reading in chunks of 4KB
                if not chunk:
                    break  # End of file reached
                # Write the chunk to the destination file
                destination_file.write(chunk)


def add_current_path_if_no_path(filename):
    # Extract the base name of the file (ignoring any path information)
    basename = os.path.basename(filename)
    
    # Compare the basename to the original filename
    # If they are the same, there was no path information in the filename
    if basename == filename:
        # Prepend the current working directory
        return os.path.join(os.getcwd(), filename)
    # If the basename and the original filename differ, path information was present
    return filename


def get_folders_diff(orig_folder, new_folder):
    if orig_folder:
        orig_files = list_all_text_files(orig_folder)
    else:
        orig_files = []

    new_files = list_all_text_files(new_folder)

    diff = {}
    for file_name in new_files:
        with open(os.path.join(new_folder, file_name), 'r') as f:
            new_file = f.read().splitlines()
        
        if file_name in orig_files:
            with open(os.path.join(orig_folder, file_name), 'r') as f:
              orig_file = f.read().splitlines()

            orig_file_name = file_name
        else:
            orig_file = []
            orig_file_name = '/dev/null'

        file_diff = difflib.unified_diff(orig_file, new_file, fromfile=orig_file_name, tofile=file_name, lineterm='')
        file_diff_str = '\n'.join(file_diff)
        if file_diff_str:
            diff[file_name] = file_diff_str

    return diff


def get_existing_files_content(build_folder, existing_files):
    existing_files_content = {}
    for file_name in existing_files:
        with open(os.path.join(build_folder, file_name), 'rb') as f:
            content = f.read()
            try:
                existing_files_content[file_name] = content.decode('utf-8')
            except UnicodeDecodeError:
                print(f"WARNING! Error loading {file_name}. File is not a text file. Skipping it.")

    return existing_files_content


def store_response_files(target_folder, response_files, existing_files):
    for file_name in response_files:
        full_file_name = os.path.join(target_folder, file_name)

        if response_files[file_name] is None:
            # None content indicates that the file should be deleted.
            if os.path.exists(full_file_name):
                os.remove(full_file_name)
                existing_files.remove(file_name)
            else:
                print(f"WARNING! Cannot delete file! File {full_file_name} does not exist.")

            continue

        os.makedirs(os.path.dirname(full_file_name), exist_ok=True)

        with open(full_file_name, "w") as f:
            f.write(response_files[file_name])

        if file_name not in existing_files:
            existing_files.append(file_name)

    return existing_files


def load_linked_resources(folder_name, resources_list):
    linked_resources = {}
    for resource in resources_list:
        file_name = resource['target']
        if file_name in linked_resources:
            continue

        full_file_name = os.path.join(folder_name, file_name)
        if not os.path.isfile(full_file_name):
            raise FileNotFoundError(f"The file '{full_file_name}' does not exist.")
    

        with open(full_file_name, 'rb') as f:
            content = f.read()
            try:
                linked_resources[file_name] = content.decode('utf-8')
            except UnicodeDecodeError:
                print(f"WARNING! Error loading {resource['text']} ({resource['target']}). File is not a text file. Skipping it.")

    return linked_resources


class TrackingFileSystemLoader(FileSystemLoader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loaded_templates = {}

    def get_source(self, environment, template_name):
        source = super().get_source(environment, template_name)
        self.loaded_templates[template_name] = source.source
        return source


def get_loaded_templates(source_path, plain_source):
    # Render the plain source with Liquid templating engine
    # to identify the templates that are being loaded
    liquid_loader = TrackingFileSystemLoader(source_path)
    liquid_env = Environment(
        loader=liquid_loader,
        undefined=StrictUndefined
    )
    plain_source_template = liquid_env.from_string(plain_source)
    try:
        plain_source_template.render()
    except UndefinedError as e:
        raise Exception(f"Undefined liquid variable: {str(e)}")

    return liquid_loader.loaded_templates
