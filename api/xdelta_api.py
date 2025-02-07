import os as _os
import subprocess as _sp
from time import sleep as _sleep


_XDELTA_PATH = ".\\"

_XDELTA = "xdelta3"


def define_xdelta_path(path) -> int:
    """redefine path for location of xdelta3.exe,

    Args:
        path (str): path of the folder where xdelta3.exe is

    Returns:
        int: 0 if xdelta3.exe has been found in this path, -1 otherwise, but the path will still be change
    """
    global _XDELTA_PATH
    if not path.endswith(_os.path.sep):
        path = _os.path.join(path, '')
    _XDELTA_PATH = path
    if not _os.path.exists(_XDELTA_PATH):
        return -1
    return 0


def _find_xdelta() -> int:
    """find exe of xdelta in XDELTA_PATH, and if found, change the value of XDELTA

    Returns:
        int: 0 in no error, -1 if xdelta exe not found
    """
    global _XDELTA
    files_exe = [file for file in _os.listdir(_XDELTA_PATH) if file.lower().endswith('.exe')]
    for file in files_exe:
        try:
            output = _sp.run([file, '--version'], stdout=_sp.PIPE, stderr=_sp.PIPE, creationflags=_sp.CREATE_NO_WINDOW)
            if "XDELTA" in str(output.stderr):
                _XDELTA = file
                return 0
        except Exception:
            continue
    return -1


def create_patch(original_file, patched_file, name_patch_file="", patch_path="", overwrite=True) -> int:
    """Create a xdelta3 patch file

    Args:
        file_no_patch (str): original file path
        file_patched (str): patched file path, so original file with modifications
        name_patch_file (str, optional): patch file name without ".xdelta" part. Defaults, name of file_no_patch.
        path_patch (str, optional): path of patch file. Defaults to exec repertory.
        overwrite (bool, optional): overwrite or not patch file. Defaults to True.

    Returns:
        int: 0 if the patch file is created, otherwise, return an error code.

    error code:
    -1 if XDELTA_PATH is not valid
    -2 if "original_file" is not found or is not a file
    -3 if "patched_file" is not found or is not a file
    -4 if the path in "patch_path" doesn't exist, or is not a folder
    -5 if xdelta exe not found
    -6 if overwrite is set to False, and the command can't overwrite an existing file
    """
    if _XDELTA_PATH != "" and not _os.path.exists(_XDELTA_PATH):
        return -1
    if not _os.path.exists(original_file) or not _os.path.isfile(original_file):
        return -2
    if not _os.path.exists(patched_file) or not _os.path.isfile(patched_file):
        return -3
    if patch_path != "" and \
       (not _os.path.exists(patch_path) or not _os.path.isdir(patch_path)):
        return -4

    if len(name_patch_file) == 0:
        name_patch_file = _os.path.splitext(_os.path.basename(original_file))[0]
    if not patch_path.endswith(_os.path.sep):
        patch_path = _os.path.join(patch_path, '')

    if _find_xdelta() != 0:
        return -5

    command = [
        _XDELTA_PATH + _XDELTA,
        "-e",  # compress
        "-s",  # source
        original_file,
        patched_file,
        patch_path + name_patch_file + ".xdelta",
    ]
    if overwrite:
        command.insert(1, "-f")
    output = _sp.run(command, stdout=_sp.PIPE, creationflags=_sp.CREATE_NO_WINDOW)
    if output.returncode != 0:
        return -5
    return output.returncode


def apply_patch(file_to_patch: str, patch_file: str, overwrite=True, name_patched_file="") -> int:
    """Create a xdelta3 patch file

    Args:
        file_to_patch (str): original file path
        patch_file (str): xdelta patch file path
        overwrite (bool, optional): overwrite or not file_to_patch file. Defaults to True.
        name_patched_file (str, optional): path of for new patched file, need to be fill if overwrite is False

    Returns:
        int: 0 if the patch file is created, otherwise, return an error code.

    error code:
    -1 if Xdelta3.exe is not found
    -2 if "file_to_patch" is not found or is not a file
    -3 if "patch_file" is not found or is not a file
    -4 if the command has a problem
    -5 if xdelta exe not found
    -6 if overwrite is False and name_patched_file is empty
    """
    def overwrite_original_file():
        _os.remove(file_to_patch)
        _sleep(0.3)
        _os.rename(name_patched_file, file_to_patch)

    if _XDELTA_PATH != "" and not _os.path.exists(_XDELTA_PATH):
        return -1
    if not _os.path.exists(file_to_patch) or not _os.path.isfile(file_to_patch):
        return -2
    if not _os.path.exists(patch_file) or not _os.path.isfile(patch_file):
        return -3

    if len(name_patched_file) == 0 and overwrite:
        splitname = _os.path.splitext(_os.path.basename(file_to_patch))
        name_patched_file = _os.path.dirname(file_to_patch) + splitname[0] + "n" + splitname[1]
    elif len(name_patched_file) == 0 and not overwrite:
        return -6

    # if _find_xdelta() != 0:
    #     return -5

    command = [
        _XDELTA_PATH + _XDELTA,
        "-f",
        "-d",  # uncompress
        "-s",  # source
        file_to_patch,
        patch_file,
        name_patched_file,
    ]
    process = _sp.run(command, stdout=_sp.PIPE, stderr=_sp.PIPE,
                      creationflags=_sp.CREATE_NO_WINDOW)

    if overwrite and process.returncode == 0:
        overwrite_original_file()
    if process.returncode != 0:
        return -4
    return process.returncode
