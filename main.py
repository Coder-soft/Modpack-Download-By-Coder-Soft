import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import os
import shutil
import re
import zipfile
import threading
import pygame

import sys
import os

def resource_path(relative_path):
    """Get the absolute path to a resource, works for both development and when bundled into an executable."""
    try:
        # PyInstaller creates a temp folder and stores the path in _MEIPASS
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


# Initialize pygame mixer
pygame.mixer.init()

# Load sound effects
click_sound = pygame.mixer.Sound(resource_path("click.mp3"))

# Define available versions and their corresponding download URLs by source
SOURCE_URLS = {
    "Modrinth": {
        "1.21": [
            "https://www.dropbox.com/scl/fo/esxa2g54h184l59i5ft8x/AAGXZFblK7q4biPjNIWcqfE?rlkey=ef8vkxcqxomohrkbzmmrtorcu&st=s96swzfb&dl=1",
            "https://www.dropbox.com/scl/fo/6fale5ezaz3b4jepa1qwe/ACfs9t5o0C1iTj6o8Zhbm2w?rlkey=qmu4sa26idv3q3ewovfwrsiz6&st=u5hxs9o7&dl=1",
            "https://www.dropbox.com/scl/fo/t26yjcdgybjgq3c08khhy/AM8WJWOkvOTL0pVQBDfdYmE?rlkey=h9cckzmqrmdfqrgk4ag1dzsv1&st=x85qtrkq&dl=1"
        ]
    }
}

# Create the main window
root = tk.Tk()
root.title("Modpack Downloader by Coder Soft")

# Set window size, prevent resizing, and set background color
root.geometry("600x220")
root.resizable(False, False)
root.configure(bg='green')

# Set default selected values
selected_version = tk.StringVar(value=list(SOURCE_URLS["Modrinth"].keys())[0])
selected_source = tk.StringVar(value="Modrinth")
default_location = os.path.expandvars(r'%AppData%\.minecraft')
selected_location = tk.StringVar(value=default_location)
status_text = tk.StringVar(value="")

def sanitize_filename(filename):
    """Sanitize the filename by removing invalid characters."""
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def download_file(url, save_folder, file_name):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        save_path = os.path.join(save_folder, file_name)
        
        print(f"Downloading to: {save_path}")
        status_text.set(f"Downloading: {file_name}")
        root.update_idletasks()
        
        with open(save_path, 'wb') as file:
            total_length = int(response.headers.get('content-length'))
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
                    downloaded += len(chunk)
                    percent_complete = downloaded / total_length * 100
                    status_text.set(f"Downloading {file_name}: {percent_complete:.2f}%")
                    root.update_idletasks()
        
        if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
            print(f"File {file_name} downloaded successfully.")
            return save_path
        else:
            print(f"File {file_name} not found after download.")
            return None
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except IOError as e:
        print(f"File I/O error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        
    return None

def extract_zip(zip_path, extract_to):
    try:
        status_text.set(f"Extracting: {os.path.basename(zip_path)}")
        root.update_idletasks()
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Extracted {zip_path} to {extract_to}")
        os.remove(zip_path)
        print(f"Deleted {zip_path}")
        return True
    except zipfile.BadZipFile as e:
        print(f"Bad zip file: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    return False

def browse_location():
    play_click_sound()
    save_folder = filedialog.askdirectory(initialdir=selected_location.get())
    if save_folder:
        entry_location.delete(0, tk.END)
        entry_location.insert(0, save_folder)
        selected_location.set(save_folder)

def delete_existing_zips(save_folder):
    zip_files = ["mods.zip", "config.zip", "resourcepacks.zip"]
    for zip_file in zip_files:
        zip_path = os.path.join(save_folder, zip_file)
        if os.path.exists(zip_path):
            os.remove(zip_path)
            status_text.set(f"Deleted existing zip file: {zip_file}")
            root.update_idletasks()
            print(f"Deleted existing zip file: {zip_path}")

def download_modpacks():
    save_folder = entry_location.get()
    if save_folder:
        if not messagebox.askyesno(
                "Warning",
                "Warning: Your mods, config, and resourcepack folders will be deleted and re-installed. Do you want to proceed?"):
            return
        
        version = selected_version.get()
        source = selected_source.get()
        urls = SOURCE_URLS.get(source, {}).get(version, [])
        file_names = ["config.zip", "mods.zip", "resourcepacks.zip"]
        success = True
        
        delete_folders(save_folder)
        delete_existing_zips(save_folder)
        
        for url, file_name in zip(urls, file_names):
            zip_path = download_file(url, save_folder, file_name)
            if zip_path is None or not extract_zip(zip_path, save_folder):
                success = False
                break

        if success:
            status_text.set("All files downloaded and extracted successfully!")
            messagebox.showinfo("Success", "All files for the selected version downloaded and extracted successfully!")
        else:
            status_text.set("Failed to download or extract some files.")
            messagebox.showerror("Error", "Failed to download or extract some files.")
    else:
        messagebox.showwarning("Warning", "Please select a save location.")

def backup_folders(base_folder):
    pass

def delete_folders(base_folder):
    folders_to_delete = [
        os.path.join(base_folder, "mods"),
        os.path.join(base_folder, "config"),
        os.path.join(base_folder, "resourcepacks")
    ]
    
    for folder in folders_to_delete:
        if os.path.exists(folder):
            status_text.set(f"Searching and Deleting: {os.path.basename(folder)}")
            root.update_idletasks()
            shutil.rmtree(folder)
            print(f"Deleted folder: {folder}")

def play_click_sound():
    click_sound.play()

def version_selected(event):
    play_click_sound()

def on_enter(e):
    e.widget.config(image=button_hover)

def on_leave(e):
    e.widget.config(image=button_normal)

def start_download():
    play_click_sound()
    download_thread = threading.Thread(target=download_modpacks)
    download_thread.start()

# Create and place source dropdown menu
tk.Label(root, text="Download Source:     ", bg='green', fg='black', font=("Minecraft fifty solid",12)).grid(row=0, column=0, padx=5, pady=5, sticky="e")
source_menu = ttk.Combobox(root, textvariable=selected_source, values=list(SOURCE_URLS.keys()), state="readonly")
source_menu.grid(row=0, column=1, padx=5, pady=5, sticky="w")

# Create and place version dropdown menu
tk.Label(root, text="Minecraft Version:   ", bg='green', fg='black', font=("Minecraft fifty solid",12)).grid(row=1, column=0, padx=5, pady=5, sticky="e")
version_menu = ttk.Combobox(root, textvariable=selected_version, values=list(SOURCE_URLS["Modrinth"].keys()), state="readonly")
version_menu.grid(row=1, column=1, padx=5, pady=5, sticky="w")

# Bind the version selection event
version_menu.bind("<<ComboboxSelected>>", version_selected)

# Create a frame for save location and browse button
frame_location = tk.Frame(root, bg='green')
frame_location.grid(row=2, column=1, padx=5, pady=5, sticky="w")

# Create and place the save location entry and browse button
tk.Label(root, text="Minecraft Directory:", bg='green', fg='black', font=("Minecraft fifty solid",12)).grid(row=2, column=0, padx=5, pady=5, sticky="e")
entry_location = tk.Entry(frame_location, width=45)
entry_location.pack(side=tk.LEFT, fill=tk.X, expand=True)
entry_location.insert(0, default_location)

# Load the images for the button textures
button_normal = tk.PhotoImage(file=resource_path("button_normal.png"))
button_hover = tk.PhotoImage(file=resource_path("button_hover.png"))

btn_browse = tk.Button(frame_location, text="...", command=browse_location, width=3, relief="raised", bg='green', fg='white')
btn_browse.pack(side=tk.LEFT)

# Create and place the download button with custom textures and sound
btn_download = tk.Button(
    root,
    text="Download",
    font=("Minecraft fifty solid", 20),
    fg="black",
    command=start_download,
    width=400,
    height=50,
    relief="flat",
    image=button_normal,
    compound="center",
    bg='green',
    activebackground='darkgreen'
)

btn_download.image = button_normal
btn_download.grid(row=3, column=0, columnspan=2, pady=10, padx=10, sticky="ew")
btn_download.bind("<Enter>", on_enter)
btn_download.bind("<Leave>", on_leave)

# Create and place the status label
status_label = tk.Label(root, textvariable=status_text, font=("Segoe UI", 8), fg="blue", bg='green')
status_label.grid(row=4, column=0, columnspan=2, pady=(2, 0))

# Run the main event loop
root.mainloop()
