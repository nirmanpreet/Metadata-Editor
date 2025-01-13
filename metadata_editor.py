import os
import time
from datetime import datetime
import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import filedialog, messagebox

# Load the Windows API functions
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

# Define necessary Windows API structures and functions
class FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", wintypes.DWORD),
                ("dwHighDateTime", wintypes.DWORD)]


def set_creation_time(file_path, creation_time):
    # Convert datetime to FILETIME
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

# Function to select a file using the file picker dialog
def select_file():
    global file_path  # Ensure file_path is accessible across functions
    file_path = filedialog.askopenfilename(title="Select a File", filetypes=(("All Files", "*.*"),))
    if file_path:
        file_path_label.config(text=f"Selected file: {file_path}")
        display_file_metadata(file_path)
        log_message(f"File selected: {file_path}")
    else:
        file_path = None
        file_path_label.config(text="No file selected")


# Function to fetch and display current file metadata
def display_file_metadata(file_path):
    try:
        stats = os.stat(file_path)
        creation_time = datetime.fromtimestamp(stats.st_ctime)
        access_time = datetime.fromtimestamp(stats.st_atime)
        modification_time = datetime.fromtimestamp(stats.st_mtime)

        # Display current metadata in the UI
        created_label.config(text=f"Created: {creation_time.strftime('%Y-%m-%d %H:%M:%S')}")
        modified_label.config(text=f"Modified: {modification_time.strftime('%Y-%m-%d %H:%M:%S')}")
        access_label.config(text=f"Last Accessed: {access_time.strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to retrieve file metadata: {str(e)}")
        log_message(f"Error retrieving metadata: {str(e)}")


# Function to update the created date (Windows only)
def update_creation_time_windows(file_path, selected_date, selected_time):
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
    if not file_path:
        messagebox.showerror("No file selected", "Please select a file first.")
        return

    # Create the editor window for creation time
    editor_window = tk.Toplevel()
    editor_window.title("Edit Created Time")
    editor_window.geometry("400x300")

    # Show current metadata for the user
    creation_time, access_time, modification_time = get_metadata(file_path)
    current_time = creation_time

    current_time_label = tk.Label(editor_window, text=f"Current Created time: {current_time}")
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


# Function to log messages in the log window
def log_message(message):
    log_text.insert(tk.END, f"{message}\n")
    log_text.yview(tk.END)


# GUI Setup
root = tk.Tk()
root.title("File Metadata Editor")
root.geometry("500x600")

# File selection section
file_path_label = tk.Label(root, text="No file selected")
file_path_label.pack(pady=5)

select_file_button = tk.Button(root, text="Select File", command=select_file)
select_file_button.pack(pady=5)

# Metadata display section
created_label = tk.Label(root, text="Created: N/A")
created_label.pack(pady=5)

modified_label = tk.Label(root, text="Modified: N/A")
modified_label.pack(pady=5)

access_label = tk.Label(root, text="Last Accessed: N/A")
access_label.pack(pady=5)

# Edit buttons section
edit_creation_button = tk.Button(root, text="Edit Creation Date", command=edit_creation_time)
edit_creation_button.pack(pady=5)

edit_modified_button = tk.Button(root, text="Edit Modified Date", command=edit_modified_time)
edit_modified_button.pack(pady=5)

# Log window section
log_text = tk.Text(root, height=10, width=60)
log_text.pack(pady=10)

# Start the GUI
root.mainloop()
