import sys
import os

# Add the project root to the Python path so all modules resolve correctly
# This is especially important when running as a PyInstaller executable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from database import initialize_database
from ui.main_window import MainWindow


def main():
    # Initialize the database and create tables on first run
    try:
        initialize_database()
    except Exception as e:
        # If the database cannot be initialized, show an error and exit
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Startup Error",
            f"Failed to initialize the database:\n\n{str(e)}\n\n"
            f"Please ensure the application has write permissions to its directory."
        )
        root.destroy()
        sys.exit(1)

    # Set global appearance before creating any window
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    # Create and launch the main window
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()