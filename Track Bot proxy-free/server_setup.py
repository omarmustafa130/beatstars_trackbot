import os
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import paramiko
import posixpath  # For handling paths consistently on remote systems (Unix-style).

def setup_server(ip, username, password):
    try:
        # Update progress
        update_progress("Connecting to the server...")
        
        # Create an SSH client
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, username=username, password=password)
        update_progress("Connected to the server.")

        # Commands to set up the server
        commands = [
            "sudo apt-get update && sudo apt-get upgrade -y",
            "sudo apt-get install -y python3",
            "sudo apt-get install -y python3-pip",
            "sudo apt-get install -y python3-venv",
            "mkdir -p /home/music_plays_bot",
            "python3 -m venv /home/music_plays_bot/music_venv",
            "source /home/music_plays_bot/music_venv/bin/activate && pip install playwright",
            "source /home/music_plays_bot/music_venv/bin/activate && playwright install firefox",
            "source /home/music_plays_bot/music_venv/bin/activate && playwright install-deps"
        ]

        # Execute setup commands
        total_steps = len(commands) + 1  # +1 for the file transfer step
        step = 1
        for command in commands:
            update_progress(f"Executing command {step}/{total_steps}: {command[:30]}...", step, total_steps)
            stdin, stdout, stderr = client.exec_command(command)
            stdin.write(password + "\n")  # For sudo password prompt if needed
            stdin.flush()
            stdout.channel.recv_exit_status()  # Ensure command completion
            step += 1

        # File transfer from "Server Files" folder
        update_progress("Transferring files...", step, total_steps)
        local_folder = "Server Files"
        remote_folder = "/home/music_plays_bot"
        sftp = client.open_sftp()

        for root, _, files in os.walk(local_folder):
            for file in files:
                local_path = os.path.join(root, file)
                relative_path = os.path.relpath(local_path, local_folder)

                # Ensure correct remote paths using posixpath
                remote_path = posixpath.join(remote_folder, relative_path.replace("\\", "/"))

                # Ensure directories exist on the remote server
                remote_directory = posixpath.dirname(remote_path)
                try:
                    sftp.chdir(remote_directory)
                except IOError:
                    mkdir_p(sftp, remote_directory)

                print(f"Copying {local_path} to {remote_path}")
                sftp.put(local_path, remote_path)

        sftp.close()
        client.close()
        update_progress("Setup and file transfer completed successfully!", total_steps, total_steps)
        messagebox.showinfo("Success", "Server setup and file transfer completed successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

def mkdir_p(sftp, remote_directory):
    """Recursive directory creation function for the remote server."""
    dirs = []
    while len(remote_directory) > 1:
        try:
            sftp.chdir(remote_directory)
            break
        except IOError:
            dirs.append(remote_directory)
            remote_directory = posixpath.dirname(remote_directory)

    while dirs:
        remote_directory = dirs.pop()
        sftp.mkdir(remote_directory)
        sftp.chdir(remote_directory)

def update_progress(message, step=0, total_steps=1):
    progress_label.config(text=message)
    progress['value'] = (step / total_steps) * 100
    root.update_idletasks()

def run_setup():
    ip = ip_entry.get()
    username = username_entry.get()
    password = password_entry.get()

    if not ip or not username or not password:
        messagebox.showwarning("Input Error", "Please fill in all fields.")
        return

    # Run the server setup in a separate thread to keep the GUI responsive
    threading.Thread(target=setup_server, args=(ip, username, password), daemon=True).start()

# Create GUI
root = tk.Tk()
root.title("Server Setup GUI")

tk.Label(root, text="Server IP:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
ip_entry = tk.Entry(root)
ip_entry.grid(row=0, column=1, padx=5, pady=5)

tk.Label(root, text="Username:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
username_entry = tk.Entry(root)
username_entry.grid(row=1, column=1, padx=5, pady=5)

tk.Label(root, text="Password:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
password_entry = tk.Entry(root, show="*")
password_entry.grid(row=2, column=1, padx=5, pady=5)

tk.Button(root, text="Run Setup", command=run_setup).grid(row=3, column=0, columnspan=2, pady=10)

progress_label = tk.Label(root, text="")
progress_label.grid(row=4, column=0, columnspan=2, pady=5)

progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
progress.grid(row=5, column=0, columnspan=2, pady=5)

root.mainloop()
