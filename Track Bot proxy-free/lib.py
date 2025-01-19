import subprocess
import sys

def install_packages_and_firefox():
    # Install necessary Python packages using pip
    packages = ["playwright", "paramiko"]
    for package in packages:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

    # Install Firefox specifically for Playwright
    subprocess.run(["playwright", "install", "firefox"], check=True)

if __name__ == "__main__":
    try:
        install_packages_and_firefox()
        print("All packages and Firefox browser installed successfully.")
    except Exception as e:
        print(f"Error during installation: {e}")
