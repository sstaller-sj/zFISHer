import tkinter as tk
import os
from PIL import Image, ImageTk
import zFISHer.config.config_manager as cfgmgr
import cv2
import numpy as np
import platform

import zFISHer.utils.config as cfg
import zFISHer.data.parameters as aparams

"""
Takes the desired nucleus image and attempts to run segementation on image. The image is 
"""


class AutoScrollbar(tk.Scrollbar):
    ''' A scrollbar that hides itself if it's not needed.
        Works only if you use the grid geometry manager '''
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
            tk.Scrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise tk.TclError('Cannot use pack with this widget')

    def place(self, **kw):
        raise tk.TclError('Cannot use place with this widget')
    
    
class SegmentationGUI(tk.Frame):
    def __init__(self, master, switch_to_new_gui, logger):
        self.master = master
        self.logger = logger
        self.switch = switch_to_new_gui  # Save the function


        self.f1_ntag = cfgmgr.get_config_value("FILE_1_NAMETAG")
        self.f2_ntag = cfgmgr.get_config_value("FILE_2_NAMETAG")
        self.f1_channels = cfgmgr.get_config_value("FILE_2_NAMETAG")

        self.f1_cs = cfgmgr.get_config_value("FILE_1_CHANNELS")
        self.f2_cs = cfgmgr.get_config_value("FILE_2_CHANNELS")

        self.processing_dir = cfgmgr.get_config_value("PROCESSING_DIR")
        self.f1_ntag = cfgmgr.get_config_value("FILE_1_NAMETAG")
        self.f2_ntag = cfgmgr.get_config_value("FILE_2_NAMETAG")

        self.f1_reg_c = self.get_reg_channel(self.f1_cs)
        self.logger.log_message(f"Channel 1 registration channel: INDEX:{self.f1_reg_c} - NAME:{self.f1_cs[self.f1_reg_c]}")
        self.f2_reg_c= self.get_reg_channel(self.f2_cs)
        self.logger.log_message(f"Channel 2 registration channel: INDEX:{self.f2_reg_c} - NAME:{self.f2_cs[self.f2_reg_c]}")   

        self.F1_base_path = os.listdir(os.path.join(os.path.join(self.processing_dir,self.f1_ntag,self.f1_cs[self.f1_reg_c],"MIP"))[0])
        self.F2_base_path = os.listdir(os.path.join(os.path.join(self.processing_dir,self.f2_ntag,self.f2_cs[self.f2_reg_c],"MIP"))[0])

        self.f1_zslices_dir = cfg.F1_C_ZSLICE_DIR_DICT[cfg.F1_REG_C]
        self.f2_zslices_dir = cfg.F2_C_ZSLICE_DIR_DICT[cfg.F2_REG_C]


        #--
        #GENERATE CONTOURS
        self.arr_nucleus_contours = None
        
        self.nucmask__init__()

        #PULL INPUT DATA
        self.arr_nucleus_contours_coordinates = self.arr_nucleus_contours       #GET NUCLEUS CONTOUR DATA from first blob detector
        self.input_img_path = os.path.join(self.processing_dir,self.f1_ntag,self.f1_cs[self.f1_reg_c],"MIP") #Path to pull drawn canvas image from
        self.masked_mip = os.path.join(self.processing_dir,"masked_dna_mip.tif") #masked MIP reference file to generate new polygon in add_polygon

        #Define polygons container to pass to DynData
        self.polygons = []      #polgons container

        self.manpolypoints = [] #x,y points container for manually drawn polygon

        #Define nucleus counter
        self.nuccount = 0


        #Initialize TKINTER frame
        tk.Frame.__init__(self, master=self.master)

        self.master.title('ZFISHER --- Nucleus Segmentation')

        # Set the initial size of the main frame
        master.geometry("1024x1022")  # Example size: width=800, height=600

        # Vertical and horizontal scrollbars for canvas
        vbar = AutoScrollbar(self.master, orient='vertical')
        hbar = AutoScrollbar(self.master, orient='horizontal')
        vbar.grid(row=0, column=1, rowspan=2, sticky='ns')
        hbar.grid(row=2, column=0, sticky='we')

        # Create canvas 
        self.canvas = tk.Canvas(self.master, highlightthickness=0,
                                xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.canvas.update()  # wait till canvas is created
        vbar.configure(command=self.scroll_y)  # bind scrollbars to the canvas
        hbar.configure(command=self.scroll_x)
        # Make the canvas expandable
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)

        mip_tomask_list = os.listdir(os.path.join(self.processing_dir,self.f1_ntag,self.f1_cs[self.f1_reg_c],"MIP"))
        mip_tomask = os.path.join(self.mip_tomask_dir,mip_tomask_list[0])
        self.input_img_path = mip_tomask

        self.image = Image.open(self.input_img_path)  # open image
        self.image = self.normalize_image(self.image)

        self.width, self.height = self.image.size
        print(self.width)
        print(self.height)
        self.baseHeight = self.height
        self.baseWidth = self.width
        self.imscale = 1.0  # scale for the canvaas image
        self.scalefactor = 1.0
        self.delta = 1.3  # zoom magnitude
        # Put image into container rectangle and use it to set proper coordinates to the image
        self.container = self.canvas.create_rectangle(0, 0, self.width, self.height, width=0)

        #---------------------------------------------------------------------------------------------------------------------------
        #MAKE CONTROL PANEL
        self.control_window = tk.Toplevel(self.master)
        self.control_window.title("Control Panel - Nucleus Segmentation")

        self.list_label = tk.Label(self.control_window, text="-----Number of Nuclei:-----")
        self.list_label.grid(row=1, column=1, columnspan=2)

        self.count_label = tk.Label(self.control_window, text="0")
        self.count_label.grid(row=2, column=1, columnspan=2)

        self.spacer_label = tk.Label(self.control_window, text="------------------------------------")
        self.spacer_label.grid(row=6, column=1, columnspan=2)  

        self.mousepos_label = tk.Label(self.control_window, text="Mouse Position: (0000.00,0000.00)", font=("Courier"))
        self.mousepos_label.grid(row=7, column=1, columnspan=2)
        x_lab = 0
        y_lab = 0
        self.mousepos_label.config(text=f"Mouse Position: ({float(x_lab):07.2f}, {float(y_lab):07.2f})")
        
        self.finish_button = tk.Button(self.control_window, text="Finalize Nuclei Picking", command=self.finalize_nucpicking)
        self.finish_button.grid(row=9, column=1, columnspan=2)     

        self.ManPoly_toggle = tk.BooleanVar(value=False)
        self.polydraw_toggle_checkbox = tk.Checkbutton(self.control_window, text="Manual Polygon", variable=self.ManPoly_toggle)
        self.polydraw_toggle_checkbox.grid(row=10, column=1, columnspan=2) 
        #---------------------------------------------------------------------------------------------------------------------------

        #BINDINGS
        self.canvas.bind('<Configure>', self.show_image)  # canvas is resized
        self.canvas.bind("<Button-1>", self.remove_polygon) #click polygon to remove
        self.canvas.bind("<Button-1>", self.man_poly_point, add='+') #add Vertex for manual polygon 

        #ADD POLYGON (RIGHT MOUSE CLICK)
        #OLD --> self.canvas.bind("<Button-2>", self.add_polygon) #click polygon to remove
        if platform.system() == "Darwin":  # macOS
            self.canvas.bind('<Button-2>', self.add_polygon) # right-click for macOS
            self.canvas.bind('<Button-2>', self.man_poly_point_complete, add='+') # close manual polygon
        elif platform.system() == "Linux":  # Linux
            self.canvas.bind('<Button-3>', self.add_polygon) # right-click for Linux
            self.canvas.bind('<Button-3>', self.man_poly_point_complete, add='+') # close manual polygon

        #DRAG (WHEEL CLICK)
        #OLD --> 
        # self.canvas.bind('<ButtonPress-3>', self.move_from)
        # self.canvas.bind('<B3-Motion>',     self.move_to)
        if platform.system() == "Darwin":  # macOS
             self.canvas.bind('<ButtonPress-3>', self.move_from)
             self.canvas.bind('<B3-Motion>',     self.move_to)
        elif platform.system() == "Linux":  # Linux
             self.canvas.bind('<ButtonPress-2>', self.move_from)
             self.canvas.bind('<B2-Motion>',     self.move_to)

        #ZOOM (MOUSEWHEEL)
        #OLD --> self.canvas.bind("<MouseWheel>", self.zoom)
        if platform.system() == "Darwin":  # macOS
            self.canvas.bind("<MouseWheel>", self.zoom)
        elif platform.system() == "Linux":  # Linux
            self.canvas.bind("<Button-4>", self.zoom)
            self.canvas.bind("<Button-5>", self.zoom)

        self.canvas.bind("<Motion>", self.motion)
        self.add_p_event_processed = False

        #Draw Nucleus POLYGONS --------------------------------------------------------------------------------------------#
        self.draw_init_polygons()
        self.show_image()

    #--FUNCTIONS---------------------------------------------------
        
        self.zoom_level = 1.0  # Initial zoom level

        self.scrollview = [0,0]


    def normalize_image(self,image):
        # Convert the image to a numpy array
        image_array = np.array(image).astype(np.float32)
        
        # Find the minimum and maximum pixel values
        min_val = image_array.min()
        max_val = image_array.max()
        
        print(f"MIN VAL {min_val}")
        print(f"MAX VAL {max_val}")
        # Normalize the image to the range [0, 1]
        normalized_array = (image_array - min_val) / (max_val - min_val)
        
        # Optionally, scale to [0, 255] for 8-bit representation
        normalized_array = (normalized_array * 255).astype(np.uint8)
        
        # Convert back to PIL Image
        normalized_image = Image.fromarray(normalized_array)
        return normalized_image
    
    def motion(self, event):
        # Calculate the mouse position in the original image
        mouse_x = self.canvas.canvasx(event.x)
        mouse_y = self.canvas.canvasy(event.y)

        #mouse_x = self.canvas.canvasx(event.x)/self.imscale
        #mouse_y = self.canvas.canvasy(event.y)/self.imscale

        #x_lab = "{:.2f}".format(mouse_x)
        #y_lab = "{:.2f}".format(mouse_y)
        x_lab = float(mouse_x)
        y_lab = float(mouse_y)
        #self.mousepos_label.config(text=f"Mouse Position: ({x_lab}, {y_lab})")
        #self.mousepos_label.config(text=f"Mouse Position: ({x_lab:03}, {y_lab:03})")
        #self.mousepos_label.config(text=f"Mouse Position: ({x_lab:6.2f}, {y_lab:6.2f})")
        self.mousepos_label.config(text=f"Mouse Position: ({float(x_lab):07.2f}, {float(y_lab):07.2f})")

    def finalize_nucpicking(self):
        self.update_nuc_count
        aparams.seg_nuc_count = self.nuccount

        
        #Set Coordinates back to base
        print(self.canvas.coords(self.container))
        print(self.bbox)


        dx = -self.canvas.coords(self.container)[0]
        dy = -self.canvas.coords(self.container)[1]
        self.canvas.move('all', dx,dy)

        #sbbox = self.canvas.bbox(self.container)
        #swidth = sbbox[2] - sbbox[0]  # Calculate width
        #sheight = sbbox[3] - sbbox[1]  # Calculate height

        self.canvas.scale('all', 0,0, 1/self.imscale, 1/self.imscale)
        #self.show_image()

        #updates polygons
        polygon_ids = self.canvas.find_withtag('polygon')

        self.polygons = []

        nucnum = 1
        for poly_id in polygon_ids:
            coords = self.canvas.coords(poly_id)
            self.polygons.append([nucnum]+ [coords])
            print(coords)
            nucnum += 1


        #nucpoly_output_array = [[row[0], self.canvas.coords(row[1])] for row in self.polygons]
        #dyn_data.nucpolygons = nucpoly_output_array
        aparams.nuc_polygons = self.polygons
       # print("ROW 1")
       # print(dyn_data.nucpolygons[0])

        print("FINISHED NUC PICK")
        #self.master.destroy()
        self.switch()
        #mainapp.toROIpick()
        

    def update_nuc_count(self):
        self.nuccount = len(self.polygons)
        self.count_label.config(text=self.nuccount)
    
   
    #DRAG (CLICK AND DRAG SCREEN)---------------------------------------------------------------------#
    def move_from(self, event):
        ''' Remember previous coordinates for scrolling with the mouse '''
        self.canvas.scan_mark(event.x, event.y)
    def move_to(self, event):
        ''' Drag (move) canvas to the new position '''
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.show_image()  # redraw the image
    
    #ZOOM---------------------------------------------------------------------------------------------#
    def zoom(self, event):
        print("scrolling")
        ''' Zoom with mouse wheel '''
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        bbox = self.canvas.bbox(self.container)  # get image area
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]: pass  # Ok! Inside the image
        else: return  # zoom only inside image area
        scale = 1.0
        # Respond to Linux (event.num) or Windows (event.delta) wheel event
        if event.num == 5 or event.delta > 0:  # scroll down
            print("down)")
            i = min(self.width, self.height)
            if int(i * self.imscale) < 30: return  # image is less than 30 pixels
            self.imscale /= self.delta
            scale        /= self.delta
        if event.num == 4 or event.delta < 0:  # scroll up
            print("up")
            i = min(self.canvas.winfo_width(), self.canvas.winfo_height())
            if i < self.imscale: return  # 1 pixel is bigger than the visible area
            self.imscale *= self.delta
            scale        *= self.delta

        print(self.imscale)
        self.canvas.scale('all', x, y, scale, scale)  # rescale all canvas objects
        self.show_image()
    #-------------------------------------------------------------------------------------------------#
    def show_image(self, event=None):
        ''' Show image on the Canvas '''
        bbox1 = self.canvas.bbox(self.container)  # get image area
        # Remove 1 pixel shift at the sides of the bbox1
        bbox1 = (bbox1[0] + 1, bbox1[1] + 1, bbox1[2] - 1, bbox1[3] - 1)
        bbox2 = (self.canvas.canvasx(0),  # get visible area of the canvas
                self.canvas.canvasy(0),
                self.canvas.canvasx(self.canvas.winfo_width()),
                self.canvas.canvasy(self.canvas.winfo_height()))
        bbox = [min(bbox1[0], bbox2[0]), min(bbox1[1], bbox2[1]),  # get scroll region box
                max(bbox1[2], bbox2[2]), max(bbox1[3], bbox2[3])]
        if bbox[0] == bbox2[0] and bbox[2] == bbox2[2]:  # whole image in the visible area
            bbox[0] = bbox1[0]
            bbox[2] = bbox1[2]
        if bbox[1] == bbox2[1] and bbox[3] == bbox2[3]:  # whole image in the visible area
            bbox[1] = bbox1[1]
            bbox[3] = bbox1[3]
        self.canvas.configure(scrollregion=bbox)  # set scroll region
        self.update_nuc_count()

        print(f"bbox1 ({bbox1[0]},{bbox1[1]},{bbox1[2]},{bbox1[3]})")
        print(f"bbox2 ({bbox2[0]},{bbox2[1]},{bbox2[2]},{bbox2[3]})")
        print(f"bbox ({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]})")
        # Store bbox1 for later use
        self.bbox1 = bbox1

        x1 = max(bbox2[0] - bbox1[0], 0)  # get coordinates (x1,y1,x2,y2) of the image tile
        y1 = max(bbox2[1] - bbox1[1], 0)
        x2 = min(bbox2[2], bbox1[2]) - bbox1[0]
        y2 = min(bbox2[3], bbox1[3]) - bbox1[1]

        #Scaled positions for adding polygons from cropchunk add_polygon func
        self.si_x1 = x1
        self.si_y1 = y1
        self.si_x2 = x2
        self.si_y2 = y2

        self.grey_image_offset_x = bbox1[0] - bbox2[0]
        self.grey_image_offset_y = bbox1[1] - bbox2[1]       

        print(f"x1,y1,x2,y2 {x1},{y1},{x2},{y2}")
        print(f"grey offset {self.grey_image_offset_x}, {self.grey_image_offset_y}")
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:  # show image if it in the visible area
            x = min(int(x2 / self.imscale), self.width)   # sometimes it is larger on 1 pixel...
            y = min(int(y2 / self.imscale), self.height)  # ...and sometimes not
            image = self.image.crop((int(x1 / self.imscale), int(y1 / self.imscale), x, y))
            imagetk = ImageTk.PhotoImage(image.resize((int(x2 - x1), int(y2 - y1))))
            self.imageid = self.canvas.create_image(max(bbox2[0], bbox1[0]), max(bbox2[1], bbox1[1]),
                                            anchor='nw', image=imagetk)
            self.bgimage= self.canvas.lower(self.imageid)  # set image into background
            self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection
        print(self.canvas.coords(self.container))
    def draw_init_polygons(self):
        prev_column_value = None
        coordinates = []
        cell_index_table = [0, 0]
        for row in self.arr_nucleus_contours_coordinates:
            #print(self.arr_nucleus_contours_coordinates)
            if prev_column_value is None or row[0] == prev_column_value:
                temp_array = row[2:]
                coordinates = np.hstack((coordinates, temp_array))
            else:
                new_row = [row[0], str(coordinates)]
                cell_index_table = np.vstack((cell_index_table, new_row))
                scaled_coordinates = [coord  if i % 2 == 0 else coord  for i, coord in
                                    enumerate(coordinates)]
                self.draw_polygon(scaled_coordinates, prev_column_value)  # Pass index to draw_polygon function
                coordinates = row[2:]
            prev_column_value = row[0]
        
        #----Remove Edge of FOV Nucs from autopick-------
        temp_polygons = []
        print(f"len temp poly {len(temp_polygons)}")
        counter = 0
        for p_row in self.polygons:
            index, polygon, indx_label = p_row

            coords = self.canvas.coords(polygon)


            heightcutoff = self.height * 0.99
            if 0 in coords:
                print("FOUND A ZERO")
                counter += 1

                self.canvas.delete(indx_label)
                self.canvas.delete(polygon)
            elif any(x >= heightcutoff for x in coords):
                print("FOUND A MAX")
                counter += 1

                self.canvas.delete(indx_label)
                self.canvas.delete(polygon)                
            else:
                temp_polygons.append(p_row)

        self.polygons = temp_polygons
        self.update_nuc_count()


    def draw_polygon(self, coordinates, index):


        index = int(index)
        self.polygons = sorted(self.polygons, key=lambda x: x[0])





        scaled_coordinates = [coord * 1 for coord in coordinates]
        #print(scaled_coordinates)
       #print(len(scaled_coordinates))
        polygon = self.canvas.create_polygon(scaled_coordinates, outline='red', fill="", tags=('polygon'))

 
        newpolycoords = self.canvas.coords(polygon)
            
        #REMOVE polygon if OVERLAPPING
        n_num_points = len(newpolycoords) // 2
        n_avg_x = sum(newpolycoords[i] for i in range(0, len(newpolycoords), 2)) / n_num_points
        n_avg_y = sum(newpolycoords[i] for i in range(1, len(newpolycoords), 2)) / n_num_points

        bboxwidth = 20
        bboxheight = 20

        n_bbox = self.canvas.create_rectangle(n_avg_x - bboxwidth/2, n_avg_y - bboxheight/2, n_avg_x + bboxwidth/2, n_avg_y + bboxheight/2)

        overlapping_items = self.canvas.find_overlapping(n_avg_x - bboxwidth/2, n_avg_y - bboxheight/2, n_avg_x + bboxwidth/2, n_avg_y + bboxheight/2)
        for item_id in overlapping_items:
            tag = self.canvas.gettags(item_id)
            if "polygon" in tag:
                if item_id != polygon: 
                    print(f"OLD POLY OVERLAP {item_id}")
                    self.canvas.delete(polygon)
                    self.canvas.delete(n_bbox)
                    return
        self.canvas.delete(n_bbox)


        #Re-index the polygon if there is a gap in the self.polygons ID list
        missing_numbers = []
        expected_number = 1
        for row in self.polygons:
            while row[0] > expected_number:
                missing_numbers.append(expected_number)
                expected_number += 1
            expected_number = row[0] + 1
        if len(missing_numbers) > 0: index = missing_numbers[0]

        print(f"polygon index {index}")
        for rowinfo in self.polygons:   # Storing index, polygon, and text index
            p_index,p_poly,p_tindex = rowinfo
            if index == p_index:
                print("dupe")


        indx_label = self.display_index_on_polygon(polygon, int(index))  # Display index on polygon

        self.polygons.append((index, polygon, indx_label))  # Storing index, polygon, and text index
        self.update_nuc_count()
        
        # Disable mouse events on the polygon
        self.canvas.tag_bind(polygon, '<Button-1>', lambda event: "break")
        self.canvas.tag_bind(polygon, '<ButtonRelease-1>', lambda event: "break")
        self.canvas.tag_bind(polygon, '<B1-Motion>', lambda event: "break")
        self.canvas.tag_bind(polygon, '<Enter>', lambda event, p=polygon: self.highlight_polygon(p))
        self.canvas.tag_bind(polygon, '<Leave>', lambda event, p=polygon: self.unhighlight_polygon(p))
    def display_index_on_polygon(self, polygon, index):
        coords = self.canvas.coords(polygon)
        x_coords = [int(coords[i]) for i in range(0, len(coords), 2)]
        y_coords = [int(coords[i]) for i in range(1, len(coords), 2)]
        x_center = sum(x_coords) // len(x_coords)  # Using integer division
        y_center = sum(y_coords) // len(y_coords)  # Using integer division
        text_item = self.canvas.create_text(x_center, y_center, text=str(index), font=('Arial', 12), fill='red')
        return text_item

    def remove_polygon(self,event):
        if self.ManPoly_toggle.get() == True: return
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y) 
        item = self.canvas.find_closest(x, y)
        if item and item[0] in (polygon[1] for polygon in self.polygons):
            for polygon_index, (index, p, ilabel) in enumerate(self.polygons):
                if p == item[0]:
                    print(f"Deleted polygon {index}")
                    self.canvas.delete(ilabel)
                    self.canvas.delete(p)  
                    print(f"polylenb {len(self.polygons)}")
                    del self.polygons[polygon_index]
                    print(f"polylena {len(self.polygons)}")
                    
                    for row in self.polygons:
                        print(row)
                    break  # Break the loop after finding the polygon to delete
        if item and item[0] in (polygon[2] for polygon in self.polygons):
            for polygon_index, (index, p, ilabel) in enumerate(self.polygons):
                if ilabel == item[0]:
                    print(f"Deleted polygon {index}")
                    self.canvas.delete(ilabel)
                    self.canvas.delete(p)  
                    print(f"polylenb {len(self.polygons)}")
                    del self.polygons[polygon_index]
                    print(f"polylena {len(self.polygons)}")
                    for row in self.polygons:
                        print(row)
                    break  # Break the loop after finding the polygon to delete
        self.update_nuc_count()

    def add_polygon(self, event):
        if self.ManPoly_toggle.get() == True: return
        mousex = self.canvas.canvasx(event.x)
        mousey = self.canvas.canvasy(event.y) 
        maskedmip = cv2.imread(self.masked_mip, cv2.IMREAD_GRAYSCALE)
        crop_width, crop_height = 300, 300  # Crop pic size

        scropx1 = max(0, int(mousex - crop_width * self.imscale // 2)) 
        scropy1 = max(0, int(mousey - crop_height * self.imscale // 2))
        scropx2 = min(maskedmip.shape[1], int(mousex + crop_width * self.imscale // 2))
        scropy2 = min(maskedmip.shape[0], int(mousey + crop_height * self.imscale // 2))

        print(f"six1_ {self.si_x1},{self.si_y1}")
        smousex = event.x_root - self.canvas.winfo_rootx()
        smousey = event.y_root - self.canvas.winfo_rooty()



        bbcoords = self.canvas.coords(self.container)

        if  self.imscale == 1.0:
            print("NO ZOOM")
            smousex = smousex*1/self.imscale + (max(bbcoords[0],self.si_x1))
            smousey = smousey*1/self.imscale + (max(self.grey_image_offset_y,self.si_y1))
        elif self.imscale > 1.0:
            print("ZOOMED IN")
            smousex = smousex*1/self.imscale + (max(self.grey_image_offset_x,self.si_x1*1/self.imscale))
            smousey = smousey*1/self.imscale + (max(self.grey_image_offset_y,self.si_y1*1/self.imscale))
        elif self.imscale < 1.0:
            print("ZOOMED OUT")
            smousex = ((smousex - max(0,self.grey_image_offset_x))*1/self.imscale) + self.si_x1*1/self.imscale
            smousey = ((smousey - max(0,self.grey_image_offset_y))*1/self.imscale) + self.si_y1*1/self.imscale


        socropx1 = max(0, int(smousex - (crop_width // 2))) 
        socropy1 = max(0, int(smousey - (crop_height // 2)))
        socropx2 = min(maskedmip.shape[0], int(smousex  + (crop_width // 2)))
        socropy2 = min(maskedmip.shape[1], int(smousey  + (crop_height // 2)))

        print(f"imscale {self.imscale}")
        print(f"grey offset {self.grey_image_offset_x}, {self.grey_image_offset_y}")
        print(f"mousepos {mousex},{mousey}")
        print(f"smousepos {smousex},{smousey}")
        print(f"scrop_ {scropx1},{scropy1},{scropx2},{scropy2}")
        print(f"socrop {socropx1},{socropy1},{socropx2},{socropy2}")
        print(f"Canvas position: x={event.x}, y={event.y}")
        print(f"Screen position: x={event.x_root}, y={event.y_root}")
        print(f"six1_{self.si_x1},{self.si_y1}")
        print(f"bbox {self.canvas.coords(self.container)}")
        canvas_position= [event.x,event.y]
        screen_position= [event.x_root, event.y_root]

       # self.canvas.create_rectangle(scropx1,scropy1,scropx2,scropy2, fill="", outline="white")

        cropped_image = maskedmip[socropy1:socropy2, socropx1:socropx2]

            #Save the cropped image
        print("cropped")
        cropfile_path = os.path.join(setup.processing_directory_folder,"cropchunk.tif")
        cv2.imwrite(cropfile_path, cropped_image) 



        #Trace the cropped image
        cropfile= cv2.imread(cropfile_path, cv2.IMREAD_GRAYSCALE)
        contours, hierarchy = cv2.findContours(cropfile, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        #print(contours)
        contoured_cropfile = cropfile.copy()
        cv2.drawContours(contoured_cropfile, contours, -1, (0,255,0), 2, cv2.LINE_AA)

        cont_cropfile_path = os.path.join(setup.processing_directory_folder,"contour_cropchunk.tif")
        cv2.imwrite(cont_cropfile_path, contoured_cropfile)

        index = 1
        isolated_count = 0
        cluster_count = 0

        arr_nucleus_contours = np.empty([1,4])

        for cntr in contours:
            epsilon = 0.001 * cv2.arcLength(cntr, True)
            approx = cv2.approxPolyDP(cntr, epsilon, True)
            n = approx.ravel() 
            i = 0
            for j in n : 
                if(i % 2 == 0): 
                    x = n[i]  
                    y = n[i + 1] 
                    #print(f"---{x},{y}")
                    #Generate contours cooridinates array to pass into tkinter visualization
                    arr_nucleus_contours = np.vstack((arr_nucleus_contours , [index,i,x,y]))
                i += 1
            index += 1
        arr_nucleus_contours = np.delete(arr_nucleus_contours,(0),axis=0)

        #print(len(arr_nucleus_contours))
        print("_________________________")
        if len(arr_nucleus_contours) <=0: 
            print("no contours found")
            self.add_p_event_processed = False
            return
        else: 

            if  self.imscale == 1.0:
                print("NO ZOOM")
                xo = scropx1
                yo = scropy1
                ofx = 0
                ofy = 0
            elif self.imscale > 1.0:
                print("ZOOMED IN")

                cmousex = self.canvas.canvasx(event.x)
                cmousey = self.canvas.canvasy(event.y)
                xo = int(cmousex - crop_width * self.imscale // 2)
                yo = int(cmousey - crop_height * self.imscale // 2)

                #self.canvas.create_oval(xo-10,yo-10,xo+10,yo+10, fill="", outline="white")

                
                ofx = 0
                ofy = 0

                bbcoords = self.canvas.coords(self.container)
                print (f"cmouse {cmousex},  -->{cmousex - crop_width*self.imscale // 2 }")

                if bbcoords[0]<0 : 
                    if (cmousex - crop_width*self.imscale // 2) < bbcoords[0]:
                        print("lilx")
                        ofx = (bbcoords[0])- (cmousex - crop_width*self.imscale // 2) 
                if bbcoords[1]<0 : 
                    print((cmousey - crop_height*self.imscale // 2))
                    if (cmousey - crop_height*self.imscale // 2) < bbcoords[1]:
                        print("lily")
                        ofy = (bbcoords[1]) - (cmousey - crop_height*self.imscale // 2) 


            elif self.imscale < 1.0:
                print("ZOOMED OUT")
                cmousex = self.canvas.canvasx(event.x)
                cmousey = self.canvas.canvasy(event.y)
                xo = int(cmousex - crop_width * self.imscale // 2)
                yo = int(cmousey - crop_height * self.imscale // 2)

              #  self.canvas.create_oval(xo-10,yo-10,xo+10,yo+10, fill="", outline="white")

                
                ofx = 0
                ofy = 0

                bbcoords = self.canvas.coords(self.container)
                print (f"cmouse {cmousex},  -->{cmousex - crop_width*self.imscale // 2 }")
                if bbcoords[0]>0 : 
                    if cmousex - crop_width*self.imscale // 2 < bbcoords[0]:
                        print("bigginx")
                        ofx = (bbcoords[0]) - (cmousex - crop_width*self.imscale // 2) 
                if bbcoords[1]>0 : 
                    if cmousey - crop_height*self.imscale // 2 < bbcoords[1]:
                        print("bigginy")
                        ofy = (bbcoords[1]) - (cmousey - crop_height*self.imscale // 2) 



                
            for row in arr_nucleus_contours:
                row[2] = row[2]*self.imscale + xo + ofx
                row[3] = row[3]*self.imscale + yo + ofy



            if len(arr_nucleus_contours) <= 0: 
                print("No contours")
                self.add_p_event_processed = False
                return
            else:
                self.draw_added_polygons(arr_nucleus_contours)

    def old_add_polygon(self, event):
        mousex = self.canvas.canvasx(event.x)
        mousey = self.canvas.canvasy(event.y) 
        maskedmip = cv2.imread(self.masked_mip, cv2.IMREAD_GRAYSCALE)
        crop_width, crop_height = 200, 200  # Crop pic size

        scropx1 = max(0, int(mousex - crop_width * self.imscale // 2)) 
        scropy1 = max(0, int(mousey - crop_height * self.imscale // 2))
        scropx2 = min(maskedmip.shape[1], int(mousex + crop_width * self.imscale // 2))
        scropy2 = min(maskedmip.shape[0], int(mousey + crop_height * self.imscale // 2))

        print(f"six1_ {self.si_x1},{self.si_y1}")
        smousex = event.x_root - self.canvas.winfo_rootx()
        smousey = event.y_root - self.canvas.winfo_rooty()





        if  self.imscale == 1.0:
            print("NO ZOOM")
            smousex = smousex*1/self.imscale + (max(self.grey_image_offset_x,self.si_x1))
            smousey = smousey*1/self.imscale + (max(self.grey_image_offset_y,self.si_y1))
        elif self.imscale > 1.0:
            print("ZOOMED IN")
            smousex = smousex*1/self.imscale + (max(self.grey_image_offset_x,self.si_x1*1/self.imscale))
            smousey = smousey*1/self.imscale + (max(self.grey_image_offset_y,self.si_y1*1/self.imscale))
        elif self.imscale < 1.0:
            print("ZOOMED OUT")
            smousex = ((smousex - max(0,self.grey_image_offset_x))*1/self.imscale) + self.si_x1*1/self.imscale
            smousey = ((smousey - max(0,self.grey_image_offset_y))*1/self.imscale) + self.si_y1*1/self.imscale


        socropx1 = max(0, int(smousex - (crop_width // 2))) 
        socropy1 = max(0, int(smousey - (crop_height // 2)))
        socropx2 = min(maskedmip.shape[0], int(smousex  + (crop_width // 2)))
        socropy2 = min(maskedmip.shape[1], int(smousey  + (crop_height // 2)))

        print(f"imscale {self.imscale}")
        print(f"grey offset {self.grey_image_offset_x}, {self.grey_image_offset_y}")
        print(f"mousepos {mousex},{mousey}")
        print(f"smousepos {smousex},{smousey}")
        print(f"scrop_ {scropx1},{scropy1},{scropx2},{scropy2}")
        print(f"socrop {socropx1},{socropy1},{socropx2},{socropy2}")
        print(f"Canvas position: x={event.x}, y={event.y}")
        print(f"Screen position: x={event.x_root}, y={event.y_root}")
        canvas_position= [event.x,event.y]
        screen_position= [event.x_root, event.y_root]
        self.canvas.create_rectangle(scropx1,scropy1,scropx2,scropy2, fill="", outline="white")

        cropped_image = maskedmip[socropy1:socropy2, socropx1:socropx2]

            #Save the cropped image
        print("cropped")
        cropfile_path = os.path.join(setup.processing_directory_folder,"cropchunk.tif")
        cv2.imwrite(cropfile_path, cropped_image) 



        #Trace the cropped image
        cropfile= cv2.imread(cropfile_path, cv2.IMREAD_GRAYSCALE)
        contours, hierarchy = cv2.findContours(cropfile, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        #print(contours)
        contoured_cropfile = cropfile.copy()
        cv2.drawContours(contoured_cropfile, contours, -1, (0,255,0), 2, cv2.LINE_AA)

        cont_cropfile_path = os.path.join(setup.processing_directory_folder,"contour_cropchunk.tif")
        cv2.imwrite(cont_cropfile_path, contoured_cropfile)

        index = 1
        isolated_count = 0
        cluster_count = 0

        arr_nucleus_contours = np.empty([1,4])

        for cntr in contours:
            epsilon = 0.001 * cv2.arcLength(cntr, True)
            approx = cv2.approxPolyDP(cntr, epsilon, True)
            n = approx.ravel() 
            i = 0
            for j in n : 
                if(i % 2 == 0): 
                    x = n[i]  + scropx1
                    y = n[i + 1]  + scropy1
                    #print(f"---{x},{y}")
                    #Generate contours cooridinates array to pass into tkinter visualization
                    arr_nucleus_contours = np.vstack((arr_nucleus_contours , [index,i,x,y]))
                i += 1
            index += 1
        arr_nucleus_contours = np.delete(arr_nucleus_contours,(0),axis=0)

        #print(len(arr_nucleus_contours))
        print(f"contours {arr_nucleus_contours}")
        print("_________________________")
        if len(arr_nucleus_contours) <=0: 
            print("no contours found")
            self.add_p_event_processed = False
            return
        else: 

            #Check if polygon is on edge of screen
            print(f"crop {scropx1},{scropy2},{scropx2},{scropy2}")
            temp_anc = arr_nucleus_contours
            keys = []
            for row in temp_anc:
                if row[0] not in keys:
                    keys.append(row[0])
            
            print(f"keys {keys}")
            for row in arr_nucleus_contours:    #[index,i,x,y]
                print(row)

                #Scale values based on scale and offset
                #NO ZOOM
                if  self.imscale == 1.0:
                #Is the crop on the edge of the screen?
                    if scropx1 <= 2 or scropy1 <=2 or scropx2 >= self.baseWidth-2 or scropy2 >= self.baseHeight-2:
                        #LEFT
                        if scropx1<= 2:
                            if row[2] >= scropx2-2 and row[3] <= scropy1+2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]                                
                                print("UPRIGHTCORNER")
                            if row[2] >= scropx2-2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]   
                                print("RIGHT")
                            if row[3] >= scropy2-2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]   
                                print("BOT")    
                            if row[3] <= scropy1+2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]   
                                print("UP")                               
                        #BOT
                        if scropy2 >= self.baseHeight-2:
                            if row[3] <= scropy1+2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]   
                                print("UPPER")
                            if row[2] <= scropx1+2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]   
                                print("LEFT")
                            if row[2] >= scropx2-2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]   
                                print("RIGHT")


                        #TOP
                        if scropy1<= 2:
                            if row[2] <= scropx1+2 and row[3] >= scropy2-2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]                                
                                print("BOTLEFTCORNER")
                            if row[2] <= scropx1+2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]   
                                print("LEFT")
                            if row[2] >= scropx2-2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]   
                                print("RIGHT")
                        #RIGHT
                        if scropx2 >= self.baseWidth-2:
                            if row[2] <= scropx1+2 and row[3] <= scropy1+2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]                                
                                print("UPLEFTCORNER")
                            if row[2] <= scropx1+2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]   
                                print("RIGHT")
                            if row[3] >= scropy2-2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]   
                                print("BOT")    
                            if row[3] <= scropy1+2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]   
                                print("UP")    
                    else:
                        if row[2] <= scropx1 or row[3] <= scropy1 or row[2] >= scropx2-2 or row[3] >= scropy2 - 2:
                            indextodelete = row[0]
                            temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]
                #ZOOMED IN
                elif self.imscale > 1.0:
                    #smousex = smousex*1/self.imscale + (max(self.grey_image_offset_x,self.si_x1*1/self.imscale))
                    #smousey = smousey*1/self.imscale + (max(self.grey_image_offset_y,self.si_y1*1/self.imscale))
                    if socropx1 <= 2 or socropy1 <=2 or socropx2 >= self.baseWidth-2 or socropy2 >= self.baseHeight-2:
                        #LEFT
                        if socropx1<= 2:
                            if row[2] >= socropx2-2 and row[3] <= socropy1+2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]                                
                                print("UPRIGHTCORNER")
                            if row[2] >= socropx2-2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]   
                                print("RIGHT")
                            if row[3] >= socropy2-2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]   
                                print("BOT")    
                            if row[3] <= socropy1+2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]   
                                print("UP")                               
                        #BOT
                        if socropy2 >= self.baseHeight-2:
                            if row[3] <= socropy1+2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]   
                                print("UPPER")
                            if row[2] <= socropx1+2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]   
                                print("LEFT")
                            if row[2] >= socropx2-2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]   
                                print("RIGHT")


                        #TOP
                        if socropy1<= 2:
                            if row[2] <= socropx1+2 and row[3] >= socropy2-2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]                                
                                print("BOTLEFTCORNER")
                            if row[2] <= socropx1+2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]   
                                print("LEFT")
                            if row[2] >= socropx2-2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]   
                                print("RIGHT")
                        #RIGHT
                        if socropx2 >= self.baseWidth-2:
                            if row[2] <= socropx1+2 and row[3] <= socropy1+2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]                                
                                print("UPLEFTCORNER")
                            if row[2] <= socropx1+2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]   
                                print("RIGHT")
                            if row[3] >= socropy2-2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]   
                                print("BOT")    
                            if row[3] <= socropy1+2:
                                indextodelete = row[0]
                                temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]   
                                print("UP")    
                    else:
                        if row[2] <= socropx1 or row[3] <= socropy1 or row[2] >= socropx2-2 or row[3] >= socropy2 - 2:
                            indextodelete = row[0]
                            temp_anc = [rowt for rowt in temp_anc if rowt[0] != indextodelete]
                
                #ZOOMED OUT
                elif self.imscale < 1.0:
                    print("ZOOMED OUT")
                   # smousex = ((smousex - max(0,self.grey_image_offset_x))*1/self.imscale) + self.si_x1*1/self.imscale
                   # smousey = ((smousey - max(0,self.grey_image_offset_y))*1/self.imscale) + self.si_y1*1/self.imscale
                    pass


            arr_nucleus_contours = temp_anc
            if len(arr_nucleus_contours) <= 0: 
                print("No contours")
                self.add_p_event_processed = False
                return
            else:
                self.draw_added_polygons(arr_nucleus_contours)

    def man_poly_point(self,event):
        if self.ManPoly_toggle.get() == False: return
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y) 
        #x,y = event.x, event.y
        self.manpolypoints.append((x,y))
        self.draw_mantemppoly()

    def man_poly_point_complete(self,event):
        if self.ManPoly_toggle.get() == False: return
        print("COMPLETE MANUAL POLYGON")
        if len(self.manpolypoints) > 2:
            #self.canvas.create_line(self.manpolypoints, fill='white', width=2, tags='tempmanpolygon')
            self.canvas.delete('tempmanpolygon')
            newindex = len(self.polygons) + 1
            self.draw_polygon(self.manpolypoints, newindex)
            self.manpolypoints = []

    def draw_mantemppoly(self):
        # Redraw polygon based on current points
        self.canvas.delete('tempmanpolygon')
        if len(self.manpolypoints) > 1:
            self.canvas.create_line(self.manpolypoints, fill='green', width=2, tags='tempmanpolygon')


    def draw_added_polygons(self,nuc_cntrs):
        #print(nuc_cntrs)
        prev_column_value = None
        coordinates = []
        cell_index_table = [0, 0]
        for row in nuc_cntrs:
            if prev_column_value is None or row[0] == prev_column_value:
                temp_array = row[2:]
                coordinates = np.hstack((coordinates, temp_array))
            else:
                new_row = [row[0], str(coordinates)]
                cell_index_table = np.vstack((cell_index_table, new_row))
                scaled_coordinates = [coord  if i % 2 == 0 else coord  for i, coord in
                                    enumerate(coordinates)]
                newindex = len(self.polygons) + 1
                    

            
                self.draw_polygon(scaled_coordinates, newindex)  # Pass index to draw_polygon function
                coordinates = row[2:]
            prev_column_value = row[0]
        scaled_coordinates = [coord if i % 2 == 0 else coord for i, coord in enumerate(coordinates)]
        newindex = len(self.polygons) + 1
        self.draw_polygon(scaled_coordinates, newindex)

        self.add_p_event_processed = False
    #------POLYGON HIGHLIGHTING-----------------------------------
    def highlight_polygon(self, polygon):
        self.canvas.itemconfig(polygon, fill='yellow')
    def unhighlight_polygon(self, polygon):
        self.canvas.itemconfig(polygon, fill='')
    #-------------------------------------------------------------  
    #-----SCROLLING CANVAS WITH SCROLLBARS------------------------    
    def scroll_y(self, *args, **kwargs):

        old_view = self.scrollview
        ''' Scroll canvas vertically and redraw the image '''
        self.canvas.yview(*args, **kwargs)  # scroll vertically
        new_view = self.canvas.yview()

        shift = (old_view[0] - new_view[0], old_view[1] - new_view[1])
        
        self.scrollview[0] += shift[0]
        self.scrollview[1] += shift[1]

        print(f"sview {self.scrollview[0]},{self.scrollview[1]}")
        self.show_image()  # redraw the image
    def scroll_x(self, *args, **kwargs):

        old_view = self.scrollview
        ''' Scroll canvas horizontally and redraw the image '''
        self.canvas.xview(*args, **kwargs)  # scroll horizontally
        new_view = self.canvas.xview()
        shift = (old_view[0] - new_view[0], old_view[1] - new_view[1])

        self.scrollview[0] += shift[0]
        self.scrollview[1] += shift[1]

        print(f"sview {self.scrollview[0]},{self.scrollview[1]}")
        self.show_image()  # redraw the image
    #-------------------------------------------------------------
    
    def get_reg_channel(self, channels):
        for index,channel in enumerate(channels):
            if channel == "DAPI":
                return index

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
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
