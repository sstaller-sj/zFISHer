

"""
Basic default zFISHer nuclei segmentation protocol using a watershed algorithm
"""

print("WE IN THE SCRIPT")

data = "passed and modified"

def nucmask__init__(self):
    self.arr_nucleus_contours = None    
    

    #Get Zslice from C0 of F1 for 
    self.slice_ismask = self.get_masking_slice()
    self.mip_tomask = self.get_MIP_tomask()
    self.generate_nucleus_mask(self.slice_ismask, self.mip_tomask)

def get_MIP_tomask(self):
    #self.mip_tomask_dir = os.path.join(self.processing_directory_folder,"FILE_1",self.p_MIP_directory,self.chanidstring)
    #self.mip_tomask_dir = os.path.join(self.processing_directory_folder,"FILE_1","RAW_MIP",self.F1_DAPI_dir)
    self.mip_tomask_dir = os.path.join(self.processing_dir,self.f1_ntag,self.f1_cs[self.f1_reg_c],"MIP")

    mip_tomask_list = os.listdir(self.mip_tomask_dir)
    mip_tomask = os.path.join(self.mip_tomask_dir,mip_tomask_list[0])
    self.input_img_path = mip_tomask

    return mip_tomask

def slice_sort_key(self, filename):
    # Extract the number between "z" and "_.tif" in the filename
    start_index = filename.find('z') + 1
    end_index = filename.find('.tif')
    number_str = filename[start_index:end_index]
    # Convert the extracted number string to an integer
    return int(number_str)
    
def get_masking_slice(self):
    # Load the f1_slices into an array
    slices = os.listdir(self.f1_zslices_dir)
    sorted_slices = sorted(slices, key=self.slice_sort_key)
    print(sorted_slices)

    self.f1_zslices_sorted = []

    for s in sorted_slices:
        path = os.path.join(self.f1_zslices_dir,s)
        sliceimage = Image.open(path)
        print(s)
        self.f1_zslices_sorted.append(sliceimage)
        print(self.f1_zslices_sorted)

    self.mid_slice_id = self.find_middle_slice(self.f1_zslices_sorted)
    
    slice_formask =f"{self.f1_ntag}_{cfg.F1_REG_C}_z{self.mid_slice_id}.tif"
    slice_formask_path = os.path.join(self.f1_zslices_dir,slice_formask)
    print(f"Slice used to mask: {slice_formask_path}")
    return slice_formask_path

def find_middle_slice(self,stack):
    middle_slice = int(len(stack)/2)
    return middle_slice

def generate_nucleus_mask(self,dapi_nucleus_mask_input,dna_mip_input):
    dapi_nucleus_base_img_in = cv2.imread(dapi_nucleus_mask_input, cv2.IMREAD_UNCHANGED)
    dapi_nucleus_base_img = dapi_nucleus_base_img_in * 255

    cv2.imwrite(os.path.join(self.processing_dir, f"dapinucleusbaseimg.tif"), dapi_nucleus_base_img_in )
    
    dapi_nucleus_base_img_8bit = cv2.convertScaleAbs(dapi_nucleus_base_img_in, alpha=(255.0/65535.0))

    cv2.imwrite(os.path.join(self.processing_dir, f"dapinucleusbaseimg2.tif"), dapi_nucleus_base_img_8bit )


    dapi_nucleus_base_img = dapi_nucleus_base_img_8bit

    dna_mip_img = cv2.imread(dna_mip_input, cv2.IMREAD_GRAYSCALE)
    gblur_img = cv2.GaussianBlur(dapi_nucleus_base_img,(35,35),0)
    ret3, nucleus_threshold_img = cv2.threshold(gblur_img,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

    # Convert nucleus_threshold_mask to uint8 if necessary
    nucleus_threshold_mask = nucleus_threshold_img.astype(np.uint8)

    # Ensure the size of the mask matches the size of the source image
    assert dna_mip_img.shape[:2] == nucleus_threshold_mask.shape[:2], "Image and mask must have the same size"

    # Apply the mask
    masked_dna_img = cv2.bitwise_and(dna_mip_img, dna_mip_img, mask=nucleus_threshold_mask)


    output_path = os.path.join(self.processing_dir, f"masked_dna_mip.tif")    
    cv2.imwrite(output_path,masked_dna_img)


    output_path = os.path.join(self.processing_dir, f"nucleus_threshold_img.tif")    
    cv2.imwrite(output_path,nucleus_threshold_img)

    #NEW -DILATE 
    kernel = np.ones((10, 10), np.uint8)  # Define a kernel for dilation; adjust size for more or less dilation
    dilated_mask = cv2.dilate(nucleus_threshold_img, kernel, iterations=1)  # Dilation
    nucleus_threshold_img = dilated_mask.copy()
    #----count cells--------

    edged_img = cv2.Canny(nucleus_threshold_img, 30,150)

    dna_mip_base = cv2.imread(dna_mip_input, cv2.COLOR_BGR2GRAY)
    contours, hierarchy = cv2.findContours(nucleus_threshold_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contoured_dna_img = dna_mip_base.copy()
    cv2.drawContours(contoured_dna_img, contours, -1, (0,255,0), 2, cv2.LINE_AA)
    print(list(contours))
    print("CONTOURS LIST)")

    index = 1
    isolated_count = 0
    cluster_count = 0
    #contoured_dna_img_1 = dna_mip_base.copy()
    #contoured_dna_img_2 = cv2.cvtColor(contoured_dna_img_1, cv2.COLOR_GRAY2BGR) * 255
    contoured_dna_img_1 = cv2.imread(dna_mip_input, cv2.IMREAD_GRAYSCALE)
    contoured_dna_img_2 = cv2.cvtColor(contoured_dna_img_1, cv2.COLOR_GRAY2BGR) *255
    #np -> [index, i , x, y]
    arr_nucleus_contours = np.empty([1,4])
    #print(arr_nucleus_contours)

    for cntr in contours:
        area = cv2.contourArea(cntr)
        convex_hull = cv2.convexHull(cntr)
        convex_hull_area = cv2.contourArea(convex_hull)
        if convex_hull_area > 0:
            ratio = area / convex_hull_area
        else: ratio = 0

        
        print(index, area, convex_hull_area, ratio)
        x,y,w,h = cv2.boundingRect(cntr)
        cv2.putText(contoured_dna_img_2, str(index), (x,y), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0,0,255), 2)
        if ratio < 0.91:
            # cluster contours in red
            cv2.drawContours(contoured_dna_img_2, [cntr], 0, (0,0,255), 2)
            cluster_count = cluster_count + 1
        else:
            # isolated contours in green
            cv2.drawContours(contoured_dna_img_2, [cntr], 0, (0,0,255), 2)
            isolated_count = isolated_count + 1

        epsilon = 0.001 * cv2.arcLength(cntr, True)
        approx = cv2.approxPolyDP(cntr, epsilon, True)
        n = approx.ravel()  
        i = 0
        font = cv2.FONT_HERSHEY_COMPLEX 
        for j in n : 
            if(i % 2 == 0): 
                x = n[i] 
                y = n[i + 1] 
    
                # String containing the co-ordinates. 
                string = str(x) + " " + str(y)

                #Generate contours cooridinates array to pass into tkinter visualization
                arr_nucleus_contours = np.vstack((arr_nucleus_contours , [index,i,x,y]))
    
                if(i == 0): 
                    # text on topmost co-ordinate. 
                    cv2.putText(contoured_dna_img_2, "Arrow tip", (x, y), 
                                    font, 0.5, (255, 0, 0))  
                else: 
                    # text on remaining co-ordinates. 
                    cv2.putText(contoured_dna_img_2, string, (x, y),  
                            font, 0.5, (0, 255, 0))  
                #print(f"index: {index} i: {i} x: {x} y: {y}")

            i = i + 1
        index = index + 1
    #print('number_clusters:',cluster_count)
    #print('number_isolated:',isolated_count)


    arr_nucleus_contours = np.delete(arr_nucleus_contours,(0),axis=0)

    #Pass to DynData Class
    self.arr_nucleus_contours = arr_nucleus_contours
    #dyn_data.arr_nucleus_contours = self.arr_nucleus_contours   

    print(arr_nucleus_contours)
    print(len(arr_nucleus_contours))

    #cell_pick_gui_main(arr_nucleus_contours)
    #---------------
    #cv2.imshow('Base Image', dapi_nucleus_base_img)
    #cv2.imshow('Gaussian Blur Image', gblur_img)
    #cv2.imshow('Threshold Nucleus Image', nucleus_threshold_img)
    #cv2.imshow('Masked DNA Image', masked_dna_img)
    #cv2.imshow('Contoured Image', contoured_dna_img)
    #cv2.imshow('Contoured2 Image',contoured_dna_img_2)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows