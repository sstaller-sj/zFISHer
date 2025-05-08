import tkinter as tk
from tkinter import filedialog

import zFISHer.utils.config as cfg
#import zFISHer.config.config_manager as cfgmgr
from zFISHer.gui.logger import Logger
import zFISHer.processing.process_nd2 as process_nd2

"""
User supplies path to the two XYZ image stacks to use for analysis.
"""

#TODO Incorporate logic to handle XYZC TIFF stack inputs

class FileInputGUI():
    """
    Window that allows user to input the the two XYZ stacks and displays file information.
    """
    

    def __init__(self, master, switch_to_new_gui):
        """
        Initialize the window for user.
        """

        self.master = master
        self.switch = switch_to_new_gui

        self.setup_window(master)
        self.set_initial_filepaths()
    

    def setup_window(self,master)->None:
        """
        Builds the GUI window and populates with widgets.

        Args:
        master (tkinter.Toplevel) : frame passed by GUImanager to build GUI.
        """

        # Window title
        self.master.title("zFISHer --- Inputs Selection")

        self.create_file_select_panel(master)
        self.create_options_panel(master)

        # Finish button
        self.set_button = tk.Button(master, text="FINALIZE INPUTS", command=self.finalize_inputs)
        self.set_button.grid(row=5, column=0, columnspan=3, pady=20)


    def create_file_select_panel(self, master) -> None:
        """
        Create panel for selected the two input files.

        Args:
        master (Tk.toplevel) : tkinter parent frame to build GUI in from GUImanager.
        """

        # Configure grid layout
        for i in range(6):  # Adjust to match the number of rows
            self.master.grid_rowconfigure(i, weight=1)
        for j in range(3):  # Adjust to match the number of columns
            self.master.grid_columnconfigure(j, weight=1)

        # Header label
        self.header_l = tk.Label(master, text="Select nd2 Files to be Analyzed", font=("Helvetica", 16, "bold"))
        self.header_l.grid(row=0, column=0, columnspan=3, sticky="nsew", pady=10)

        # File 1 widgets
        self.f1_l = tk.Label(master, text="FILE 1 (FIXED):")
        self.f1_l.grid(row=1, column=0, sticky="e", padx=10, pady=5)

        self.f1_path_e = tk.Entry(master, width=50)
        self.f1_path_e.grid(row=1, column=1, sticky="ew", padx=10, pady=5)

        self.f1_button = tk.Button(master, text="Browse", command=self.open_file_1)
        self.f1_button.grid(row=1, column=2, padx=10, pady=5)

        # File 2 widgets
        self.f2_l = tk.Label(master, text="FILE 2 (MOVING):")
        self.f2_l.grid(row=2, column=0, sticky="e", padx=10, pady=5)

        self.f2_path_e = tk.Entry(master, width=50)
        self.f2_path_e.grid(row=2, column=1, sticky="ew", padx=10, pady=5)

        self.f2_button = tk.Button(master, text="Browse", command=self.open_file_2)
        self.f2_button.grid(row=2, column=2, padx=10, pady=5)
    

    def create_options_panel(self, master) -> None:
        """
        Create panel to the user define choices for analysis

        Args:
        master (Tk.toplevel) : tkinter parent frame to build GUI in from GUImanager.
        """

        self.options_frame = tk.Frame(master)
        self.options_frame.grid(row=1, column=10)

        # FRAME FILE HEADERS
        f1_header = tk.Label(self.options_frame, text="FILE 1 (FIXED IMAGE):")
        f1_header.grid(row=2, column=5, padx=10, pady=5)
        f2_header = tk.Label(self.options_frame, text="FILE 2 (MOVING IMAGE):")
        f2_header.grid(row=2, column=10, padx=10, pady=5)


        # FILE NAMETAG ENTRY
        ntag_description = tk.Label(self.options_frame, text="File Nametag:")
        ntag_description.grid(row=4, column=2, sticky="e", padx=10, pady=5)

        self.f1_ntag_e = tk.Entry(self.options_frame, width=20)
        self.f1_ntag_e.grid(row=4, column=5, padx=10, pady=5)
        self.f1_ntag_e.insert(0, "F1")
        self.f2_ntag_e = tk.Entry(self.options_frame, width=20)
        self.f2_ntag_e.grid(row=4, column=10, padx=10, pady=5)
        self.f2_ntag_e.insert(0, "F2")

        # FILE REG CHANNEL SELECTION
        reg_c_description = tk.Label(self.options_frame, text="XYZ Registration Channel:")
        reg_c_description.grid(row=6, column=2, sticky="e", padx=10, pady=5)
        # Create a Tkinter StringVar to store the selected channel
        self.f1_reg_c_var = tk.StringVar()
        self.f2_reg_c_var = tk.StringVar()
        self.f1_reg_c_var.set(None)  # Set the default selected channel to the first in the list
        self.f2_reg_c_var.set(None)

        # Create the dropdown menu (OptionMenu)
        self.f1_reg_c_dd = tk.OptionMenu(self.options_frame, self.f1_reg_c_var, 'NONE')
        self.f1_reg_c_dd.grid(row=6, column=5, padx=10, pady=5)
        self.f2_reg_c_dd = tk.OptionMenu(self.options_frame, self.f2_reg_c_var, 'NONE')
        self.f2_reg_c_dd.grid(row=6, column=10, padx=10, pady=5)

        # Bind the on_channel_select function to the dropdown menu event (when selection changes)
        self.f1_reg_c_var.trace_add("write", self.on_channel_select)
        self.f2_reg_c_var.trace_add("write", self.on_channel_select)

        # FILE SEGMENTATION CHANNEL SELECTION
        seg_c_description = tk.Label(self.options_frame, text="Nuclei Segmentation Channel:")
        seg_c_description.grid(row=8, column=2, sticky="e", padx=10, pady=5)

        # Create a Tkinter StringVar to store the selected SEG channel
        self.f1_seg_c_var = tk.StringVar()
        self.f2_seg_c_var = tk.StringVar()
        self.f1_seg_c_var.set(None)  # Set the default selected channel to the first in the list
        self.f2_seg_c_var.set(None)

        # Create the SEG dropdown menu (OptionMenu)
        self.f1_seg_c_dd = tk.OptionMenu(self.options_frame, self.f1_seg_c_var, 'NONE')
        self.f1_seg_c_dd.grid(row=8, column=5, padx=10, pady=5)
        self.f2_seg_c_dd = tk.OptionMenu(self.options_frame, self.f2_seg_c_var, 'NONE')
        self.f2_seg_c_dd.grid(row=8, column=10, padx=10, pady=5)

        # Bind the on_channel_select function to the dropdown menu event (when selection changes)
        self.f1_seg_c_var.trace_add("write", self.on_channel_select)
        self.f2_seg_c_var.trace_add("write", self.on_channel_select)


        # FILE SEGMENTATION CHANNEL SELECTION
        seg_c_algo_description = tk.Label(self.options_frame, text="Nuclei Segmentation Algorithm:")
        seg_c_algo_description.grid(row=8, column=2, sticky="e", padx=10, pady=5)

    def on_channel_select(self, *args):
        """
        Update options widgets after user selects input file path.
        """

        pass


    def set_initial_filepaths(self):
        if cfg.F1_PATH == None or cfg.F1_PATH == None == "":
            pass
        else:
            self.f1_path_e.delete(0, tk.END)
            self.f1_path_e.insert(0, cfg.F1_PATH)
        if cfg.F2_PATH == None or cfg.F2_PATH == None == "":
            pass
        else:
            self.f2_path_e.delete(0, tk.END)
            self.f2_path_e.insert(0, cfg.F2_PATH == None)    



      #  if cfgmgr.get_config_value("FILE_1_PATH") == None or cfgmgr.get_config_value("FILE_1_PATH") == "":
       #     pass
       # else:
       #     self.f1_path_e.delete(0, tk.END)
       #     self.f1_path_e.insert(0, cfgmgr.get_config_value("FILE_1_PATH"))
       # if cfgmgr.get_config_value("FILE_2_PATH") == None or cfgmgr.get_config_value("FILE_2_PATH") == "":
       #     pass
       # else:
       #     self.f2_path_e.delete(0, tk.END)
       #     self.f2_path_e.insert(0, cfgmgr.get_config_value("FILE_2_PATH"))    


    def open_file_1(self):
        """
        Update file 1 path entry widget with selected path name.
        """
        filepath = filedialog.askopenfilename()
        self.f1_path_e.delete(0, tk.END)
        self.f1_path_e.insert(0, filepath)
        self.set_file_select()


    def open_file_2(self):
        """
        Update file 2 path entry widget with selected path name.
        """
        filepath = filedialog.askopenfilename()
        self.f2_path_e.delete(0, tk.END)
        self.f2_path_e.insert(0, filepath)
        self.set_file_select()


    def set_file_select(self):
        """
        Creates option menu after filepaths are specified.
        """

        self.get_display_information()
        self.update_display()


    def get_display_information(self):
        """
        Pull information from nd2 files for display to user.
        """
        f1_filepath = self.f1_path_e.get()
        f2_filepath = self.f2_path_e.get()
        print(f"FILE 1 and FILE 2 FILEPATHS: {f1_filepath} ---- {f2_filepath}")

        if f1_filepath and f1_filepath.endswith(".nd2"):
            self.f1_metadata: dict = process_nd2.nd2_metadata_processor(f1_filepath)
        else:
            print("Invalid or missing FILE 1 path.")

        if f2_filepath and f2_filepath.endswith(".nd2"):
            self.f2_metadata: dict = process_nd2.nd2_metadata_processor(f2_filepath)
        else:
            print("Invalid or missing FILE 2 path.")


    def update_display(self):
        """
        Set the display information of the selected files and options.
        """
        if not hasattr(self, 'f1_metadata') or not hasattr(self, 'f2_metadata'):
            print("File metadata is incomplete. Skipping display update.")
            return

        f1_c_list = self.f1_metadata['c_list']
        f2_c_list = self.f2_metadata['c_list']

        self.f1_reg_c_dd.destroy()
        self.f2_reg_c_dd.destroy()

        self.f1_reg_c_dd = tk.OptionMenu(self.options_frame, self.f1_reg_c_var, *f1_c_list)
        self.f2_reg_c_dd = tk.OptionMenu(self.options_frame, self.f2_reg_c_var, *f2_c_list)

        self.f1_reg_c_dd.grid(row=6, column=5, padx=10, pady=5)
        self.f2_reg_c_dd.grid(row=6, column=10, padx=10, pady=5)

        self.dd_dapi_check(f1_c_list, f2_c_list)



    def dd_dapi_check(self,f1_c_list,f2_c_list):
        """
        If DAPI is detected in dropdowns, automatically set dropdown selection to that channel.
        """

        # Check for 'DAPI' or 'dapi' in f1_c_list and set it
        for item in f1_c_list:
            if item.lower() == 'dapi':  # Case-insensitive comparison
                self.f1_reg_c_var.set(item)  # Set the exact item found (preserve case)
                self.f1_seg_c_var.set(item)
                break

        # Check for 'DAPI' or 'dapi' in f2_c_list and set it
        for item in f2_c_list:
            if item.lower() == 'dapi':  # Case-insensitive comparison
                self.f2_reg_c_var.set(item)  # Set the exact item found (preserve case)
                self.f2_seg_c_var.set(item)
                break


    def finalize_inputs(self):
        """
        Terminal point of the GUI after files and 
        options are selected to proceed in pipeline.
        Updates information in config.
        """

        # Pass variables from file metadata
        cfg.F1_PATH = self.f1_path_e.get() 
        cfg.F2_PATH = self.f2_path_e.get() 
        cfg.F1_NTAG = self.f1_ntag_e.get()
        cfg.F2_NTAG = self.f2_ntag_e.get()
        cfg.F1_C_LIST = self.f1_metadata['c_list']
        cfg.F2_C_LIST = self.f2_metadata['c_list']
        cfg.F1_C_NUM = self.f1_metadata['c_num']
        cfg.F2_C_NUM = self.f2_metadata['c_num']
        cfg.F1_Z_NUM = self.f1_metadata['z_num']
        cfg.F2_Z_NUM = self.f2_metadata['z_num']
        
        # Pass user-defined options
        cfg.F1_REG_C = self.f1_reg_c_var.get()
        cfg.F2_REG_C = self.f2_reg_c_var.get()
        cfg.F1_SEG_C = self.f1_seg_c_var.get()
        cfg.F2_SEG_C = self.f2_seg_c_var.get()

        # Switch to the next GUI passed by GUImanager
        self.switch()      
