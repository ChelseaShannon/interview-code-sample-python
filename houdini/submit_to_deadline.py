import os
import shutil
from datetime import datetime
import hou

# Globals
FARM_FOLDER = "//shared_drive/project/renders/"


class SubmitToDeadline():
    '''
    Base class to handle submitting to Deadline. Includes copying files to Truenas, so that Deadline can find all valid files.
    Requires subclasses for each application to handle application-specific requirements.
    '''

    def __init__(self, this_file, filename):
        '''
        Initialize SubmitToDeadline object.

        Args:
            this_file (str): Path to the current file.
            filename (str): Name of the current file.
        '''
        self.this_file = this_file
        self.filename = filename
        
        # Private
        self._destination_folder = None
        self._submitted = False

    
    def get_render_folder(self):
        '''
        Return the already created destination folder for the files to be rendered.
        Throw an error if not already created.

        Returns:
            str: Destination folder path.
        '''
        if not self._destination_folder:
            raise RuntimeError("No folder has been created yet for render. Need to run create destination folder first")        
        
        return self._destination_folder
    
    
    def create_render_folder(self):
        '''
        Create the directory to hold the render files on shared drive.

        Returns:
            str: Destination folder path.
        '''

        # TODO: add logging for last submitted destination path if self._submitted = True
        
        _now = datetime.now()
        TIME = _now.strftime("%Y%m%d_%H%M%S")

        dst_folder = os.path.join(FARM_FOLDER, f"{TIME}_{self.filename}")
        os.makedirs(dst_folder, exist_ok=False)

        self._destination_folder = dst_folder
        return self._destination_folder

    
    def copy_file_for_render(self, src, dst):
        '''
        Copy the given file to the destination folder for rendering.

        Args:
            src (str): Source file path.
            dst (str): Destination file path.
        
        Returns:
            bool: True if the file is successfully copied, False otherwise.
        '''
        try:
            shutil.copyfile(src, dst)
            return True
        except Exception as e:
            os.makedirs(dst, exist_ok=True)
            shutil.copyfile(src, dst)
            return True
        raise RuntimeError(f"Didn't copy from {src} to {dst}")

   
    def save_and_duplicate_this_file(self):
        '''
        Save the current file and save to the render folder.
        '''
        raise NotImplementedError


    def copy_dependencies(self):
        '''
        Copy dependency files to the render folder.
        '''
        raise NotImplementedError


    def trigger_submit(self):
        '''
        Trigger the submission to Deadline.
        '''
        raise NotImplementedError

    
    def trigger_remote_submit(self):
        '''
        Trigger the remote submission to Deadline.
        '''
        raise NotImplementedError
    
    
    def doIt(self, from_open_GUI=True, dryrun=False, dependency_files=[]):
        '''
        Main command to submit to Deadline.

        Args:
            from_open_GUI (bool): True if submit is triggered from an open application, False if triggered from the command line.
            dryrun (bool): True to perform all processes except actually submitting to Deadline.
            dependency_files (list): List of files to copy to the render location.

        Raises:
            RuntimeError: If copy dependency files and dependency to location have unequal number of values.
        '''

        dst_folder = self.create_render_folder()

        if from_open_GUI:
            self.save_and_duplicate_this_file()
        else:
            self.copy_file_for_render(self.this_file, dst_folder)
            
        if dependency_files:
            self.copy_dependencies(dependency_files)
        else:
            raise RuntimeError("Copy Dependency Files and Dependency To location must have equal number of values")
        
        if not dryrun:
            self.trigger_submit()


class HoudiniSubmit(SubmitToDeadline):
    
    def __init__(self, this_file=None, filename=None):
        '''
        Initialize HoudiniSubmit object.

        Args:
            this_file (str, optional): Path to the current file. Defaults to None.
            filename (str, optional): Name of the current file. Defaults to None.
        '''
        self.this_file = this_file if this_file else hou.expandString("$HIPFILE")
        self.filename = filename if filename else hou.expandString("$HIPNAME")
    

    def save_and_duplicate_this_file(self):
        '''
        Save the current Houdini file and save to the render folder.
        '''
        destination_folder = self.get_render_folder()

        render_location = os.path.join(destination_folder, f"{self.filename}.hip")
        
        hou.hipFile.save()
        hou.hipFile.save(render_location)

    
    def get_file_references(self, error_if_external_refs=True):
        '''
        Get file references in the current Houdini scene.

        Args:
            error_if_external_refs (bool): True to raise error if external references are found, False otherwise.

        Returns:
            list: List of file dependencies.
        '''
        warnings = ''
        dependencies = []
        current_folder = hou.expandString("$HIP")

        for parm, path in hou.fileReferences():

            if path in current_folder:
                if path in parm.rawValue():
                    relative_path = path.replace(current_folder, '$HIP')
                    parm.set
