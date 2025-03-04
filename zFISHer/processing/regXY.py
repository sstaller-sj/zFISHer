import os
import numpy as np
import zFISHer.config.config_manager as cfgmgr
from PIL import Image, ImageTk
from pystackreg import StackReg
import cv2
import zFISHer.utils.config as cfg
from zFISHer.gui.logger import Logger
from skimage.registration import phase_cross_correlation
from skimage.metrics import structural_similarity as ssim
import matplotlib.pyplot as plt
from scipy.ndimage import shift


"""
Algorithm for simple 2D XY registration using two MIPs from the input files.
"""


def start_regXY(f1_c,f2_c):
    """
    File 
    """
    f1_reg_img = load_reg_img(f1_c,1)
    f2_reg_img = load_reg_img(f2_c,2)
    f1_reg_img_n = normalize_img(f1_reg_img)
    f2_reg_img_n = normalize_img(f2_reg_img)
    f1_reg_img_gs = grayscale_img(f1_reg_img_n)
    f2_reg_img_gs = grayscale_img(f2_reg_img_n)
    offset = registerXY(f1_reg_img_gs,f2_reg_img_gs)
    #register = RegisterXY()

def load_reg_img(img_c,f_num):
    if f_num ==1:
        img_path = cfg.F1_C_MIP_DIR_DICT[img_c]
    else:
        img_path = cfg.F2_C_MIP_DIR_DICT[img_c]

    file = os.listdir(img_path)[0]
    full_path = os.path.join(img_path,file)
    image = Image.open(full_path)

    return image

def normalize_img(img):
    # Convert the image to a numpy array
    img_array = np.array(img).astype(np.float16)
    
    # Find the minimum and maximum pixel values
    min_val = img_array.min()
    max_val = img_array.max()
    
    print(f"MIN VAL: {min_val}")
    print(f"MAX VAL: {max_val}")
    
    # Normalize the image to the range [0, 1]
    normalized_array = (img_array - min_val) / (max_val - min_val)
    
    # Scale to [0, 65535] for 16-bit representation
    normalized_array = (normalized_array * 65535).astype(np.uint16)
    
    # Convert back to PIL Image
    normalized_img = Image.fromarray(normalized_array)      

    return normalized_img

def grayscale_img(image):
# Convert PIL Image to numpy array
    image_array = np.array(image)
    
    # Check if the image has 3 dimensions (indicating an RGB image)
    if image_array.ndim == 3:
        # Convert RGB to grayscale by averaging the channels
        image_array = np.mean(image_array, axis=2)
    
    return image_array

def registerXY(img_1, img_2):
    # Perform translation transformation
    sr = StackReg(StackReg.TRANSLATION)
    reg = sr.register_transform(img_1, img_2)

    # Clip the registered result to ensure no negative values
    reg = reg.clip(min=0)

    offset = sr.get_matrix()[:2, 2]
    print(f"Offset for XY registration: {offset}")
    print(sr.get_matrix())

    offset[0] = (-offset[0])
    offset[1] = (-offset[1])


    cfgmgr.set_config_value("X_OFFSET",offset[0])
    cfgmgr.set_config_value("Y_OFFSET",offset[1])

    cfg.OFFSET_X = offset[0]
    cfg.OFFSET_Y = offset[1]

    return offset
