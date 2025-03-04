import os
from zFISHer import version

"""
Holds all data to be referenced and updated across modules.
"""

# Version of the zFISHer software
VERSION = version

# Created directory paths for reference
BASE_DIR = None
OUTPUT_DIR = None
PROCESSING_DIR = None
LOGS_DIR = None

F1_PROCESSING_DIR = None
F2_PROCESSING_DIR = None

F1_C_DIR_LIST = [] # folder inside each file's processing directory named by channel
F2_C_DIR_LIST = []

F1_C_MIP_DIR_DICT = {}  # key channel name (string) : value is path (string)
F2_C_MIP_DIR_DICT = {}

F1_C_ZSLICE_DIR_DICT = {} # key channel name (string) : value is path (string)
F2_C_ZSLICE_DIR_DICT = {}

# Input XYZ file paths 
F1_PATH = None
F2_PATH = None

# Displayed and saved nickname of input file
F1_NTAG = None
F2_NTAG = None

# List of channel names (string)
F1_C_LIST = None
F2_C_LIST = None

# Number of channels
F1_C_NUM = None
F2_C_NUM = None

# Number of z-slices
F1_Z_NUM = None
F2_Z_NUM = None

# Channel to use for XYZ registration
F1_REG_C = None
F2_REG_C = None

# Offset of File 2 relative to File 1 XYZ
OFFSET_X = None # in pixels
OFFSET_Y = None # in pixels
OFFSET_Z = None # in z-slices



def set_file_paths(self):
    self._instance.base_dir = "/path/to/base/dir"
    self._instance.output_dir = "/path/to/output"
    cls._instance.processing_dir = "/path/to/processing"
    cls._instance.logs_dir = "/path/to/logs"

