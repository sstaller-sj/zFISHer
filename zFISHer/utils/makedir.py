import os
import logging
from datetime import datetime

import zFISHer.utils.config as cfg
#import zFISHer.config.config_manager as cfgmgr  #TODO REMOVE

"""
Make directories for pipeline processing and sets their paths for reference in the config file.
"""


def set_core_dir_values() -> None:
    """
    Set the primary directories for reference by app modules.
    """
    
    # These are the directories to generate analysis files
    BASE_DIR = os.getenv("BASE_DIR",os.path.abspath(os.getcwd()))
    OUTPUT_DIR = os.getenv("OUTPUT_DIR",os.path.join(BASE_DIR, "OUTPUT"))
    PROCESSING_DIR = os.getenv("PROCESSING_DIR",os.path.join(BASE_DIR, OUTPUT_DIR, "processing"))
    LOGS_DIR = os.getenv("LOGS_DIR",os.path.join(BASE_DIR, OUTPUT_DIR, "logs"))

  


    #cfg.BASE_DIR = BASE_DIR
    cfg.OUTPUT_DIR = OUTPUT_DIR
    cfg.PROCESSING_DIR = PROCESSING_DIR
    cfg.LOGS_DIR = LOGS_DIR
    #cfgmgr.set_config_value("BASE_DIR",BASE_DIR)    #TODO REMOVE
    #cfgmgr.set_config_value("OUTPUT_DIR",OUTPUT_DIR)#TODO REMOVE
    #cfgmgr.set_config_value("PROCESSING_DIR",PROCESSING_DIR)#TODO REMOVE
    #cfgmgr.set_config_value("LOGS_DIR",LOGS_DIR)#TODO REMOVE


def make_output_directories(self):
    """
    Creates core directories that the analysis pipeline will populate.
    """

    '''
    os.makedirs(cfgmgr.get_config_value("OUTPUT_DIR"), exist_ok=True)
    os.makedirs(cfgmgr.get_config_value("PROCESSING_DIR"), exist_ok=True)
    os.makedirs(cfgmgr.get_config_value("LOGS_DIR"), exist_ok=True)
    '''
    pass


def make_processing_directories():
    """
    Creates each file's channel directories in the processing folder.
    """

    # Create directories for file 1 and file 2
    os.makedirs(cfg.F1_PROCESSING_DIR, exist_ok=True)
    os.makedirs(cfg.F2_PROCESSING_DIR, exist_ok=True)       
    
    # Create directories for file 1 and file 2 channels
    for dir in cfg.F1_C_DIR_LIST:
        os.makedirs(dir, exist_ok=True)
    for dir in cfg.F2_C_DIR_LIST:
        os.makedirs(dir, exist_ok=True)

    # Create z-slice directories per channel
    for dir in cfg.F1_C_ZSLICE_DIR_DICT.values():
         os.makedirs(dir, exist_ok=True)
    for dir in cfg.F2_C_ZSLICE_DIR_DICT.values():
         os.makedirs(dir, exist_ok=True)

    # Create MIP directories per channel
    for dir in cfg.F1_C_MIP_DIR_DICT.values():
         os.makedirs(dir, exist_ok=True)
    for dir in cfg.F2_C_MIP_DIR_DICT.values():
         os.makedirs(dir, exist_ok=True)

    # Create processing segmentation directory
    os.makedirs(cfg.SEG_PROCESSING_DIR, exist_ok=True)
