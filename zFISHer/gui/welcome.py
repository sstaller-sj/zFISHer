import tkinter as tk
from zFISHer import version

"""
The entry point window GUI when the application is initialized.
"""

class WelcomeWindowGUI():
    def __init__(self, master, switch_to_gui_two):
        self.master = master
        self.master.title("ZFISHER --- Welcome")
        
        # Get screen size dynamically
        screen_width, screen_height = self.get_screen_size()
        print(f"Screen Size: {screen_width}x{screen_height}")

        # Set window size (optional: use the full screen size)
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)

        # Calculate the position to center the window
        x_offset = (screen_width // 2) - (window_width // 2)
        y_offset = (screen_height // 2) - (window_height // 2)

        # Set window geometry (size and position)
        self.master.geometry(f"{window_width}x{window_height}+{x_offset}+{y_offset}")
        self.master.config(bg="#121212")

        # Configure the grid to center the buttons
        master.grid_rowconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=1)
        master.grid_rowconfigure(2, weight=1)
        master.grid_columnconfigure(0, weight=1)
        master.grid_columnconfigure(1, weight=1)
        master.grid_columnconfigure(2, weight=1)

        # Add widgets
        self.titlelabel = tk.Label(master, text=f"Welcome to ZFISHER v{version.__version__}!", background="black", 
                                   foreground="white", font=("Helvetica", 35))
        self.titlelabel.grid(row=0, column=1, sticky="nsew", padx=0, pady=20)

        self.imageprocessbutton = tk.Button(master, text="Begin Analysis",  
                                            command=lambda: self.tofileselect(switch_to_gui_two),
                                            background="black", foreground="green", font=("Helvetica", 20))
        self.imageprocessbutton.grid(row=1, column=1, sticky="nsew", padx=30, pady=30)

        master.protocol("WM_DELETE_WINDOW", self.disable_close)

    def tofileselect(self, switch) -> None:
        switch()

    def disable_close(self) -> None:
        """
        Prevents the window from closing when the 'X' button is clicked.
        """
        print("Window close disabled.")  # Optionally print a message

    def get_screen_size(self) -> None:
        """
        Fetch the screen width and height dynamically.
        """
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        return screen_width, screen_height