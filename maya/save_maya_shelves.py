#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This is a sample script which manages Maya shelves including loading, reloading, and saving shelves to Perforce.

By default maya loads shelves under your local maya folder. It can be useful keeping local files during dev and updating p4 
when a release version is ready.

"""

import os
import re
import shutil
import maya.cmds as cmds

from P4 import P4, P4Exception
from p4util.connection import P4ConnectionHandler
from p4util.submitter import P4Submitter

from constants import GLOBAL_SHELF_DIR, LOCAL_SHELF_DIR, PRESET_SHELF_DIR

# Define the order in which shelves should appear
SHELF_ORDER = ['Shotgrid', 'vm_AI', 'vm_Assets', 'vm_Metahumans', 'vm_Rigging', 'vm_AnimTools', 'vm_Utils', 'Custom']


# Utility Functions
def is_directory(path_to_check):
    """Return True if the given string is a directory."""
    return os.path.isdir(path_to_check)


def is_shelf_file(file_name):
    """Return True if the file name matches the convention of a Maya shelf file."""
    return re.match(r"^shelf_\S*\.mel", file_name)


def extract_short_shelf_name(shelf_file):
    """Extract the short name of the shelf file (without the "shelf_" prefix and ".mel" suffix)."""
    return re.findall(r"^shelf_(\S*?)\.mel", shelf_file)[0]


def concat_long_shelf_name(short_shelf_name):
    """Concatenate the long shelf name from the short shelf name."""
    return f"shelf_{short_shelf_name}.mel"


def sort_shelves_from_ref_list(shelf_list):
    """
    Sort the list of shelf names with those found in the reference SHELF_ORDER list.
    """
    reference_list = SHELF_ORDER

    # Define a custom key function to handle missing values
    def custom_key(elem):
        try:
            return reference_list.index(elem)
        except ValueError:
            # If the element is not found in the reference list, return a large index
            return len(reference_list)

    # Sort the original list based on the order of elements in the reference list
    sorted_list = sorted(shelf_list, key=custom_key)
    return sorted_list


# Shelf Management Functions
def get_shelf_dir_by_context(shelf_context):
    """
    Return the directory path of the Maya shelf location based on the context (local, preset, global).
    """
    directories = {
        'local': LOCAL_SHELF_DIR,
        'preset': PRESET_SHELF_DIR,
        'global': GLOBAL_SHELF_DIR
    }
    
    shelf_directory = directories.get(shelf_context, 'Invalid keyword')

    if shelf_context == 'Invalid keyword':
        raise RuntimeError(f"Invalid shelf context selected. Select from {directories.keys()}")
    
    if not is_directory(shelf_directory):
        raise RuntimeError(f"{shelf_directory} is not a directory. Check constants file for values.")

    return shelf_directory


def get_ordered_shelves(shelf_context):
    """
    Get the ordered list of shelves in a shelf directory.
    """
    shelf_directory = get_shelf_dir_by_context(shelf_context)
    shelf_list = []

    for filename in os.listdir(shelf_directory):
        if is_shelf_file(filename):
            shelf_name = extract_short_shelf_name(filename)
            shelf_list.append(shelf_name)

    ordered_list = sort_shelves_from_ref_list(shelf_list)
    return ordered_list


# File Operations Functions
def get_full_shelf_path(short_shelf_name, shelf_context):
    """
    Get the full path of the shelf given the short name and shelf context.
    """
    full_shelf_name = concat_long_shelf_name(short_shelf_name)
    shelf_dir = get_shelf_dir_by_context(shelf_context)

    file_path = os.path.join(shelf_dir, full_shelf_name)

    return file_path


def copy_local_shelf_to_global_location(local_shelf_path, global_shelf_path):
    """
    Copy the local shelf file to the global shelf location.
    """
    shutil.copyfile(local_shelf_path, global_shelf_path)


# Perforce Operations Functions
def get_tool_ws():
    """
    Get the Perforce workspace.
    """
    handler = P4ConnectionHandler()
    wss = handler._get_workspaces()
    tool_ws = ''
    owner = ''

    for ws in wss:
        if '_tools' in ws['client']:
            tool_ws = ws['client']
            owner = ws['Owner']

    return tool_ws, owner

def show_checked_out_dialog():
        """
        Display dialog that explains that the P4 file is already checked out by another user.
        
        # TODO add which user has the file checked out.

        """
        result = cmds.confirmDialog(
            title='File Checked Out',
            message='The file is checked out by another user.',
            button=['Cancel'],
            defaultButton='Cancel',
            cancelButton='Cancel',
            dismissString='Cancel'
        )

        return result

def checkout_p4_file(p4, global_shelf_path):
    """
    Checkout a file from Perforce.
    """
    file_info = p4.run("fstat", global_shelf_path)[0]
    opened_files = p4.run('opened', global_shelf_path)

    is_checked_out = bool(opened_files)

    if not is_checked_out:  # Sync and check it out
        p4.run("sync", global_shelf_path)
        p4.run("edit", global_shelf_path)

        file_info = p4.run("files", global_shelf_path)
        if not file_info:
            p4.run("add", global_shelf_path)  # Add the file to Perforce if not already added

    else:
        # Checked out by someone else, simply tell the user about it.
        if opened_files['user'] != p4.user:
            show_checked_out_dialog()
            return False
        
        else:  # Checked out by current user
            current_version = file_info['haveRev']
            versions = file_info['headRev']
            
            is_latest_version = current_version == versions

            if not is_latest_version:
                p4.run("sync", global_shelf_path)

    return True


def submit_file_to_perforce(p4, global_shelf_path, local_shelf_path):
    """
    Submit the file to Perforce.
    """
    p4 = P4()
    p4.exception_level = 1

    p4.client, p4.user,  = get_tool_ws()
        
    description = f"Updates to shelf {global_shelf_path}" ## TODO Add UI dialog for user input

    try:
        p4.connect()
        checkout_success = checkout_p4_file(p4, global_shelf_path)
        if not checkout_success:
            return False
        
        copy_local_shelf_to_global_location(local_shelf_path, global_shelf_path)

        file_diff = p4.run("diff", global_shelf_path)
        
        if not file_diff:
            # No changes detected, revert the file
            p4.run("revert", global_shelf_path)
            return False
        else:
            # Changes detected, submit changes
            p4.run("submit", "-d", description)
            return True
        
    except P4Exception as e:
        print(f"Perforce error: {e}")
        return False
    finally:
        p4.disconnect()


# UI Class for saving shelves
class SaveShelf:
    def __init__(self):
        self.window = cmds.window(title='Save Shelf')
        column = cmds.columnLayout()

        self.shelf_menu = cmds.optionMenuGrp(label='Save Shelf to P4', columnWidth=(2, 150))
        cmds.separator(h=5, style="none")
        cmds.separator(h=2, style="out")

        self.save_context_option

    def __init__(self, title, menu_items):
        self.title = title
        self.menu_items = menu_items

    def create_dialog(self):
        self.window = cmds.window(title=self.title)
        self.layout = cmds.columnLayout(adjustableColumn=True)
        
        # Add menu to the dialog
        self.menu = cmds.optionMenu(label='Select Shelf:', parent=self.layout)
        for item in self.menu_items:
            cmds.menuItem(label=item, parent=self.menu)
        
        # Add buttons
        self.button_layout = cmds.rowLayout(numberOfColumns=2, columnWidth2=(100, 100), columnAlign=(1, 'center'))
        self.save_button = cmds.button(label='Save', width=100, command=self.save_callback)
        self.cancel_button = cmds.button(label='Cancel', width=100, command=self.cancel_callback)
        
        cmds.showWindow(self.window)


class SaveShelfDialog:
    def __init__(self, title, menu_items):
        self.title = title
        self.menu_items = menu_items

        self.window = None
        self.menu = None
        self.save_button = None
        self.cancel_button = None

    def create_dialog(self):
        if self.window is not None:
            cmds.deleteUI(self.window)

        self.window = cmds.window(title=self.title)
        self.layout = cmds.columnLayout(adjustableColumn=True)
        
        # Add menu to the dialog
        self.menu = cmds.optionMenu(label='Select Shelf:', parent=self.layout)
        for item in self.menu_items:
            cmds.menuItem(label=item, parent=self.menu)

        cmds.separator(h=5, style="none")
        cmds.separator(h=2, style="out")

        self.save_context_option = cmds.checkBox(label='Local Save Only', align='left')
        
        # Add buttons
        self.button_layout = cmds.rowLayout(numberOfColumns=2, columnWidth2=(100, 100), columnAlign=(1, 'center'))
        self.save_button = cmds.button(label='Save', width=100, command=self.save_callback)
        self.cancel_button = cmds.button(label='Cancel', width=100, command=self.cancel_callback)
        
        cmds.showWindow(self.window)

    def save_callback(self, *args):
        selected_item = cmds.optionMenu(self.menu, query=True, value=True)

        self.local_shelf_path = get_full_shelf_path(selected_item, "local")
        saved = self.save_local_shelf()

        if not saved:
            try_again = self.ask_to_try_again()
            while try_again:
                self.save_callback()

        self.local_save_only = cmds.checkBox(self.save_context, query = True, value = True)

        if self.local_save_only:
            self.show_success_dialog()
            
        else: # Submit to perforce
            self.global_shelf_path = get_full_shelf_path(selected_item, "local")
            depot_save = submit_file_to_perforce(self.global_shelf_path)

            if depot_save:
                return True
            else:
                raise RuntimeError(f"Error saving shelf to perforce. Check location {self.global_shelf_path}")


    def cancel_callback(self, *args):
        cmds.deleteUI(self.window)

    def save_local_shelf(self):
        return cmds.saveShelf(self.local_shelf_path)

    def ask_to_try_again(self):
        """
        User may have another maya scene open.
        """
        msg = "Failed to save shelf locally. Probably because another Maya scene is open. " \
            "Try closing other Maya files."
        
        buttons = ['Try Again', 'Cancel']
        result = cmds.confirmDialog(title='Failed to Save Shelf Tool',
                                    message=msg,
                                    button=buttons,
                                    defaultButton='Try Again',
                                    cancelButton='Cancel',
                                    dismissString='Cancel')

        if result == 'Try Again':
            return True
        
        elif result == 'Cancel':
            self.cancel_callback()
            return False
        
        else:
            return False
        
    def show_success_dialog(self):
        """
        Dialog for user feedback that save was successful.

        """
        cmds.confirmDialog(title='Success', message=f'Successful Save of Shelf {self.local_shelf_path}',
                               button=['Ok'], defaultButton='Ok', cancelButton='Ok')
            
        self.cancel_callback()

def main():
    local_shelves = get_ordered_shelves("local")
    dialog = SaveShelfDialog('Save Shelf', local_shelves)
    dialog.create_dialog()

# Call main function
main()