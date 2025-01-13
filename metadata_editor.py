import os
import time
from datetime import datetime
import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import filedialog, messagebox

# Load the Windows API functions
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

# Define necessary Windows API structures and functions for setting file creation time
class FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", wintypes.DWORD),
                ("dwHighDateTime", wintypes.DWORD)]

def set_creation_time(file_path, creation_time):
    """
    This function sets the creation time for a file on Windows by interacting with the Windows API.
    The creation time is passed as a datetime object, which is converted to the appropriate FILETIME format.
    """
    ft = FILETIME()
    timestamp = int(creation_time.timestamp() * 10000000) + 116444736000000000  # Convert to Windows epoch
    ft.dwLowDateTime = timestamp & 0xFFFFFFFF
    ft.dwHighDateTime = (timestamp >> 32) & 0xFFFFFFFF

    # Open the file with required permissions
    handle = kernel32.CreateFileW(file_path, 
                                  0x40000000,  # GENERIC_WRITE
                                  0,            # No sharing
                                  None,         # Security attributes
                                  3,            # OPEN_EXISTING
                                  0,            # No additional flags
                                  None)

    if handle == -1:
        raise ctypes.WinError(ctypes.get_last_error())

    # Set the file creation time using Windows API
    if kernel32.SetFileTime(handle, ctypes.byref(ft), None, None) == 0:
        raise ctypes.WinError(ctypes.get_last_error())

    # Close the file handle
    kernel32.CloseHandle(handle)

def get_metadata(file_path):
    """
    This function retrieves the metadata for the given file. It returns the creation,
    modification, and access times as datetime objects.
    """
    try:
        stats = os.stat(file_path)
        creation_time = datetime.fromtimestamp(stats.st_ctime)  # Creation time
        access_time = datetime.fromtimestamp(stats.st_atime)  # Last access time
        modification_time = datetime.fromtimestamp(stats.st_mtime)  # Modification time
        return creation_time, access_time, modification_time
    except Exception as e:
        raise Exception(f"Error retrieving metadata for {file_path}: {str(e)}")

# Function to select a file using the file picker dialog
def select_file():
    """
    This function opens a file picker dialog for the user to select a file. The selected file path
    is displayed on the GUI, and its current metadata (creation, modification, last access times) is fetched.
    """
    global file_path  # Ensure file_path is accessible across functions
    file_path = filedialog.askopenfilename(title="Select a File", filetypes=(("All Files", "*.*"),))
    if file_path:
        file_path_label.config(text=f"Selected file: {file_path}")
        display_file_metadata(file_path)
        log_message(f"File selected: {file_path}")
    else:
        file_path = None
        file_path_label.config(text="No file selected")


# Function to update the creation time (Windows only)
def update_creation_time_windows(file_path, selected_date, selected_time):
    """
    This function updates the creation date of a file on Windows using the Windows API.
    It converts the selected date and time to a datetime object, then calls the API to set the creation time.
    """
    try:
        # Combine the selected date and time into a datetime object
        date_str = f"{selected_date} {selected_time}"
        new_datetime = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

        # Update the file creation time using the Windows API
        set_creation_time(file_path, new_datetime)

        messagebox.showinfo("Success", f"Successfully updated creation time for {file_path} to {new_datetime}")
        log_message(f"Updated creation time for {file_path} to {new_datetime}")
        display_file_metadata(file_path)  # Refresh the metadata display
    except Exception as e:
        messagebox.showerror("Error", f"Error updating creation time: {str(e)}")
        log_message(f"Error updating creation time: {str(e)}")


# Function to update the modified date and also update last accessed date
def update_modified_time(file_path, selected_date, selected_time):
    """
    This function updates the modified time of a file and sets the last accessed time to the same value.
    The selected date and time are converted to a datetime object and used to update the timestamps.
    """
    try:
        # Combine the selected date and time into a datetime object
        date_str = f"{selected_date} {selected_time}"
        new_datetime = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

        # Update the modified date (st_mtime)
        os.utime(file_path, (os.stat(file_path).st_atime, new_datetime.timestamp()))

        # Also update the last accessed date to match the new modified date
        os.utime(file_path, (new_datetime.timestamp(), new_datetime.timestamp()))

        messagebox.showinfo("Success", f"Modified time and Last Accessed time updated to {new_datetime}")
        log_message(f"Updated modified and last accessed time for {file_path} to {new_datetime}")
        display_file_metadata(file_path)  # Refresh the metadata display
    except Exception as e:
        messagebox.showerror("Error", f"Error updating modified time: {str(e)}")
        log_message(f"Error updating modified time: {str(e)}")


# Function to open the editing window for updating the creation time
def edit_creation_time():
    """
    This function opens a window where the user can select a new creation date and time for the selected file.
    It validates the date and time input and updates the file's creation time accordingly.
    """
    if not file_path:
        messagebox.showerror("No file selected", "Please select a file first.")
        return

    # Retrieve the metadata (creation, access, modification times)
    creation_time, access_time, modification_time = get_metadata(file_path)

    # Create the editor window for creation time
    editor_window = tk.Toplevel()
    editor_window.title("Edit Created Time")
    editor_window.geometry("400x300")

    current_time_label = tk.Label(editor_window, text=f"Current Created time: {creation_time}")
    current_time_label.pack(pady=10)

    # Date Entry
    date_label = tk.Label(editor_window, text="Select Date (YYYY-MM-DD):")
    date_label.pack()
    date_entry = tk.Entry(editor_window)
    date_entry.insert(0, creation_time.strftime("%Y-%m-%d"))
    date_entry.pack(pady=5)

    # Time Entry
    time_label = tk.Label(editor_window, text="Select Time (HH:MM:SS):")
    time_label.pack()
    time_entry = tk.Entry(editor_window)
    time_entry.insert(0, creation_time.strftime("%H:%M:%S"))
    time_entry.pack(pady=5)

    # Save button to update created time
    def save_creation_time():
        selected_date = date_entry.get()
        selected_time = time_entry.get()

        # Validate the date and time format
        try:
            datetime.strptime(selected_date, "%Y-%m-%d")
            time.strptime(selected_time, "%H:%M:%S")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid date and time.")
            return

        # Update the creation time (which will also update the modified time)
        if os.name == 'nt':  # Windows OS
            update_creation_time_windows(file_path, selected_date, selected_time)
        else:
            update_modified_time(file_path, selected_date, selected_time)

        editor_window.destroy()

    save_button = tk.Button(editor_window, text="Save Changes", command=save_creation_time)
    save_button.pack(pady=10)

    # Cancel button
    cancel_button = tk.Button(editor_window, text="Cancel", command=editor_window.destroy)
    cancel_button.pack()

    editor_window.mainloop()


# Function to open the editing window for updating the modified time
def edit_modified_time():
    """
    This function opens a window where the user can select a new modified date and time for the selected file.
    It updates both the modified time and the last accessed time with the new values.
    """
    if not file_path:
        messagebox.showerror("No file selected", "Please select a file first.")
        return

    # Create the editor window for modified time
    editor_window = tk.Toplevel()
    editor_window.title("Edit Modified Time")
    editor_window.geometry("400x300")

    # Show current metadata for the user
    creation_time, access_time, modification_time = get_metadata(file_path)
    current_time = modification_time

    current_time_label = tk.Label(editor_window, text=f"Current Modified time: {current_time}")
    current_time_label.pack(pady=10)

    # Date Entry
    date_label = tk.Label(editor_window, text="Select Date (YYYY-MM-DD):")
    date_label.pack()
    date_entry = tk.Entry(editor_window)
    date_entry.insert(0, current_time.strftime("%Y-%m-%d"))
    date_entry.pack(pady=5)

    # Time Entry
    time_label = tk.Label(editor_window, text="Select Time (HH:MM:SS):")
    time_label.pack()
    time_entry = tk.Entry(editor_window)
    time_entry.insert(0, current_time.strftime("%H:%M:%S"))
    time_entry.pack(pady=5)

    # Save button to update modified time
    def save_modified_time():
        selected_date = date_entry.get()
        selected_time = time_entry.get()

        # Validate the date and time format
        try:
            datetime.strptime(selected_date, "%Y-%m-%d")
            time.strptime(selected_time, "%H:%M:%S")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid date and time.")
            return

        # Update the modified time and last accessed time
        update_modified_time(file_path, selected_date, selected_time)
        editor_window.destroy()

    save_button = tk.Button(editor_window, text="Save Changes", command=save_modified_time)
    save_button.pack(pady=10)

    # Cancel button
    cancel_button = tk.Button(editor_window, text="Cancel", command=editor_window.destroy)
    cancel_button.pack()

    editor_window.mainloop()


# Function to display file metadata
def display_file_metadata(file_path):
    """
    This function displays the file's current metadata (creation, access, and modification times) on the GUI.
    """
    try:
        creation_time, access_time, modification_time = get_metadata(file_path)

        metadata_label.config(text=f"Creation Time: {creation_time}\n"
                                  f"Last Accessed: {access_time}\n"
                                  f"Last Modified: {modification_time}")
    except Exception as e:
        metadata_label.config(text=f"Error fetching metadata: {str(e)}")
        log_message(f"Error fetching metadata: {str(e)}")


# Function to log messages in the log box
def log_message(message):
    """
    This function writes messages to the log box in the GUI for tracking operations.
    """
    log_box.insert(tk.END, message + "\n")
    log_box.yview(tk.END)


# Create the main window
root = tk.Tk()
root.title("File Metadata Editor")
root.geometry("500x600")

file_path_label = tk.Label(root, text="No file selected", width=50, anchor="w")
file_path_label.pack(pady=10)

# Buttons to select a file and edit metadata
select_file_button = tk.Button(root, text="Select File", command=select_file)
select_file_button.pack(pady=10)

edit_creation_button = tk.Button(root, text="Edit Creation Date", command=edit_creation_time)
edit_creation_button.pack(pady=5)

edit_modified_button = tk.Button(root, text="Edit Modified Date", command=edit_modified_time)
edit_modified_button.pack(pady=5)

# Metadata display
metadata_label = tk.Label(root, text="File Metadata will be displayed here.", justify="left", width=50)
metadata_label.pack(pady=10)

# Log box for live logs
log_label = tk.Label(root, text="Live Log:")
log_label.pack(pady=5)

log_box = tk.Text(root, height=10, width=50)
log_box.pack(pady=10)

# Start the main loop
root.mainloop()
