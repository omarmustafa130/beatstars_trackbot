import subprocess

def run_install_script():
    try:
        result = subprocess.run(["python", "lib.py"], check=True)
        print("Script executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running the script: {e}")

if __name__ == "__main__":
    run_install_script()
