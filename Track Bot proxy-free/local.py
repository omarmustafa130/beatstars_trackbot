import tkinter as tk
import json
import paramiko
import os

CONFIG_FILE = "gui_input_config.json"

def save_inputs(host, password, url, min_duration, max_duration, repeat_count, use_proxy, ip_change_interval, num_instances):
    config = {
        "host": host,
        "password": password,
        "url": url,
        "min_duration": min_duration,
        "max_duration": max_duration,
        "repeat_count": repeat_count,
        "use_proxy": use_proxy,
        "ip_change_interval": ip_change_interval,
        "num_instances": num_instances
    }
    with open(CONFIG_FILE, 'w') as config_file:
        json.dump(config, config_file)

def load_inputs():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as config_file:
            return json.load(config_file)
    return {}

def run_remote_script(host, password, url, min_duration, max_duration, repeat_count, use_proxy, ip_change_interval, num_instances):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=host, username="root", password=password)

        params = {
            "url": url,
            "min_duration": min_duration,
            "max_duration": max_duration,
            "repeat_count": repeat_count,
            "headless": True,
            "use_proxy": use_proxy,
            "ip_change_interval": ip_change_interval
        }
        params_json = json.dumps(params)

        config_file_path = "/home/music_plays_bot/config_crox.json"
        sftp = ssh.open_sftp()
        with sftp.file(config_file_path, 'w') as config_file:
            config_file.write(params_json)
        sftp.close()

        remote_command = "/home/music_plays_bot/main_no_gui_croxy.py"

        for count in range(num_instances):
            nohup_command = f"setsid bash -c 'source /home/music_plays_bot/music_venv/bin/activate && python3 {remote_command}' > /home/music_plays_bot/output_crox_{count+1}.log 2>&1 &"

            print(f"Executing command: {nohup_command}")
            stdin, stdout, stderr = ssh.exec_command(nohup_command)
            print("Output (if any):")
            for line in iter(stdout.readline, ""):
                print(line, end="")
            print("Errors (if any):")
            for line in iter(stderr.readline, ""):
                print(line, end="")

        ssh.close()
    except Exception as e:
        print(f"An error occurred: {e}")

def start_gui():
    def on_run():
        host = host_entry.get()
        password = password_entry.get()
        url = url_entry.get()
        min_duration = int(min_duration_entry.get())
        max_duration = int(max_duration_entry.get())
        repeat_count = int(repeat_count_entry.get())
        use_proxy = use_proxy_var.get()
        ip_change_interval = int(ip_change_interval_entry.get()) if use_proxy else 0  # Only use interval if proxy is enabled
        num_instances = int(num_instances_entry.get())

        save_inputs(host, password, url, min_duration, max_duration, repeat_count, use_proxy, ip_change_interval, num_instances)

        run_remote_script(host, password, url, min_duration, max_duration, repeat_count, use_proxy, ip_change_interval, num_instances)

    def toggle_ip_interval_state():
        if use_proxy_var.get():
            ip_change_interval_entry.configure(state='normal')
        else:
            ip_change_interval_entry.configure(state='disabled')

    saved_inputs = load_inputs()

    root = tk.Tk()
    root.title("Remote Track Player Control")

    tk.Label(root, text="Server IP Address:").grid(row=0, column=0, padx=5, pady=5)
    host_entry = tk.Entry(root, width=40)
    host_entry.grid(row=0, column=1, padx=5, pady=5)
    host_entry.insert(0, saved_inputs.get("host", ""))

    tk.Label(root, text="SSH Password:").grid(row=1, column=0, padx=5, pady=5)
    password_entry = tk.Entry(root, show="*", width=40)
    password_entry.grid(row=1, column=1, padx=5, pady=5)
    password_entry.insert(0, saved_inputs.get("password", ""))

    tk.Label(root, text="Enter URL:").grid(row=2, column=0, padx=5, pady=5)
    url_entry = tk.Entry(root, width=50)
    url_entry.grid(row=2, column=1, padx=5, pady=5)
    url_entry.insert(0, saved_inputs.get("url", ""))

    tk.Label(root, text="Min Duration (seconds):").grid(row=3, column=0, padx=5, pady=5)
    min_duration_entry = tk.Entry(root)
    min_duration_entry.grid(row=3, column=1, padx=5, pady=5)
    min_duration_entry.insert(0, saved_inputs.get("min_duration", 1))

    tk.Label(root, text="Max Duration (seconds):").grid(row=4, column=0, padx=5, pady=5)
    max_duration_entry = tk.Entry(root)
    max_duration_entry.grid(row=4, column=1, padx=5, pady=5)
    max_duration_entry.insert(0, saved_inputs.get("max_duration", 10))

    tk.Label(root, text="Number of Repeats:").grid(row=5, column=0, padx=5, pady=5)
    repeat_count_entry = tk.Entry(root)
    repeat_count_entry.grid(row=5, column=1, padx=5, pady=5)
    repeat_count_entry.insert(0, saved_inputs.get("repeat_count", 1))

    tk.Label(root, text="Use Proxy:").grid(row=6, column=0, padx=5, pady=5)
    use_proxy_var = tk.BooleanVar(value=saved_inputs.get("use_proxy", False))
    use_proxy_checkbox = tk.Checkbutton(root, text="Enable", variable=use_proxy_var, command=toggle_ip_interval_state)
    use_proxy_checkbox.grid(row=6, column=1, padx=5, pady=5)

    tk.Label(root, text="Change IP After Repeats:").grid(row=7, column=0, padx=5, pady=5)
    ip_change_interval_entry = tk.Entry(root)
    ip_change_interval_entry.grid(row=7, column=1, padx=5, pady=5)
    ip_change_interval_entry.insert(0, saved_inputs.get("ip_change_interval", 1))
    ip_change_interval_entry.configure(state='normal' if use_proxy_var.get() else 'disabled')

    tk.Label(root, text="Number of Instances:").grid(row=8, column=0, padx=5, pady=5)
    num_instances_entry = tk.Entry(root)
    num_instances_entry.grid(row=8, column=1, padx=5, pady=5)
    num_instances_entry.insert(0, saved_inputs.get("num_instances", 1))

    run_button = tk.Button(root, text="Run", command=on_run)
    run_button.grid(row=9, column=0, columnspan=2, pady=10)

    root.mainloop()

start_gui()
