# Sample Code: DCC Utilities

## Table of Contents:
1. [Houdini](#houdini)
   - [submit_to_deadline.py](#submit_to_deadlinepy)
2. [Maya](#maya)
   - [save_maya_shelves.py](#save_maya_shelvespy)
   - [constants.py](#constantspy)
3. [Unreal Engine](#unreal-engine)
   - [example_structure.json](#example_structurejson)
   - [generate_folder_structure.py](#generate_folder_structurepy)

---

## Houdini <a name="houdini"></a>

### `submit_to_deadline.py` <a name="submit_to_deadlinepy"></a>
This Python script provides functionalities to submit Houdini files to Deadline for rendering. It includes methods for creating render folders, copying files, and triggering the submission process. The script is designed as a utility for automating the rendering workflow in Houdini projects.

---

## Maya <a name="maya"></a>

### `save_maya_shelves.py` <a name="save_maya_shelvespy"></a>
This Python script is designed for Maya and facilitates the saving of custom shelf configurations. It enables users to store and manage custom shelf setups for easier access to frequently used tools and functionalities within Maya. The script serves as a utility to streamline the customization of Maya environments.

### `constants.py` <a name="constantspy"></a>
The `constants.py` file contains predefined constant values used across Maya-related scripts. It centralizes commonly used constants, making them easily accessible and modifiable for consistent behavior across multiple scripts. This file is intended as a utility to maintain uniformity and ease of maintenance in Maya scripting projects.

---

## Unreal Engine <a name="unreal-engine"></a>

### `example_structure.json` <a name="example_structurejson"></a>
The `example_structure.json` file serves as a template for defining a structured directory hierarchy in Unreal Engine projects. It outlines a standardized folder organization scheme tailored for organizing assets and resources within Unreal Engine projects. This JSON file provides a sample structure for new projects, offering utility in maintaining a consistent organizational framework.

### `generate_folder_structure.py` <a name="generate_folder_structurepy"></a>
This Python script automates the creation of folder structures in Unreal Engine projects based on the specifications outlined in the `example_structure.json` file. It traverses the JSON structure and generates corresponding folders within the project directory, streamlining the initial setup process for new projects. The script is intended as a utility for project setup and organization in Unreal Engine development.
