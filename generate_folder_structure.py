import unreal
import json
import os

class FolderCreator:
    def __init__(self, json_filename):
        '''
        Initialize FolderCreator object.

        Args:
            json_filename (str): Name of the JSON file containing folder structure.
        '''
        self.json_filename = json_filename

    def create_folders(self, root_path, structure):
        '''
        Recursively create folders based on the provided structure.

        Args:
            root_path (str): Root path where folders will be created.
            structure (dict): Dictionary containing folder structure.
        '''
        for key, value in structure.items():
            folder_path = os.path.join(root_path, key)
            if not unreal.EditorAssetLibrary.does_directory_exist(folder_path):
                unreal.EditorAssetLibrary.make_directory(folder_path)
                unreal.log("Created folder: {}".format(folder_path))
            if isinstance(value, dict):
                self.create_folders(folder_path, value)

    def main(self):
        '''
        Main function to create folders based on the JSON file.
        '''
        # Get the directory of the current script
        script_dir = os.path.dirname(__file__)

        # Construct the full path to the JSON file
        json_file_path = os.path.join(script_dir, self.json_filename)

        # Load JSON data
        with open(json_file_path, "r") as file:
            structure = json.load(file)

        # Root content folder path in Unreal
        root_content_path = "/Game/"

        # Create folders recursively
        self.create_folders(root_content_path, structure)

if __name__ == "__main__":
    # Create an instance of FolderCreator and execute main function
    folder_creator = FolderCreator("example_structure.json")
    folder_creator.main()
