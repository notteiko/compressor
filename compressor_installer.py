import os
import sys
import ctypes
import subprocess
import urllib.request
import zipfile
import winreg as reg

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def relaunch_as_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit()

def download_file(url, out_path):
    def reporthook(blocks, block_size, total_size):
        if total_size <= 0:
            return
        downloaded = blocks * block_size
        percent = int(downloaded * 100 / total_size)
        mb_downloaded = downloaded / (1024 ** 2)
        mb_total = total_size / (1024 ** 2)
        print(f"\rDownloading: {mb_downloaded:.2f}/{mb_total:.2f} MB [{percent}%]", end="")

    print(f"Downloading {os.path.basename(out_path)} from {url}")
    urllib.request.urlretrieve(url, out_path, reporthook)
    print("\nDownload complete.")

def extract_ffmpeg(zip_path, target_dir):
    print("Extracting FFmpeg...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(target_dir)
    print(f"FFmpeg extracted to {target_dir}")

def run_installer(path):
    print(f"Running installer: {path}")
    try:
        subprocess.run([path], check=True)
        print(f"{os.path.basename(path)} installation completed.")
    except Exception as e:
        print(f"Installation failed: {e}")

def main():
    if not is_admin():
        print("Re-launching as administrator...")
        relaunch_as_admin()
    app_folder = os.path.join(os.environ["LOCALAPPDATA"], "Compressor")
    os.makedirs(app_folder, exist_ok=True)
    file_path = os.path.join(app_folder, "compressor.py")
    url = "https://raw.githubusercontent.com/notteiko/compressor/refs/heads/main/compressor3.py"
    print(f"Stahujem script z: {url}\ndo {file_path}")
    urllib.request.urlretrieve(url, file_path)
    print("Stiahnuty")

    extension_list = [".mov", ".mp4", ".mkv", ".avi", ".webm"]
    print("Zapisujem do registy:")
    for extension in extension_list:
        with reg.CreateKey(reg.HKEY_CURRENT_USER, f"Software\\Classes\\SystemFileAssociations\\{extension}\\shell\\Compress") as key:
            reg.SetValue(key, "", reg.REG_SZ, "Compress and Trim")
            print(f"Software\\Classes\\SystemFileAssociations\\{extension}\\shell\\Compress")
        with reg.CreateKey(reg.HKEY_CURRENT_USER, f"Software\\Classes\\SystemFileAssociations\\{extension}\\shell\\Compress\\command") as key:
            reg.SetValue(key, "", reg.REG_SZ, f'pyw "{sys.argv[0]}" "%1"')
            print(f"Software\\Classes\\SystemFileAssociations\\{extension}\\shell\\Compress\\command")

    try:
        subprocess.check_output(["python", "--version"])
    except:
        print("Stahujem Python")
        python_url = "https://www.python.org/ftp/python/3.12.1/python-3.12.1-amd64.exe"
        python_dir = os.path.join(os.environ["TEMP"], "python.exe")
        download_file(python_url, python_dir)
        os.system(python_dir + " /quiet InstallAllUsers=1 PrependPath=1")
        print("Instalujem Python...")
        

    try:
        subprocess.check_output(["ffmpeg", "-version"])
    except:
        print("Instalujem FFmpeg")
        ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        ffmpeg_zip = os.path.join(os.environ["TEMP"], "ffmpeg.zip")
        ffmpeg_dir = os.path.join(os.environ["ProgramFiles"], "ffmpeg")
        download_file(ffmpeg_url, ffmpeg_zip)
        if not os.path.exists(ffmpeg_dir):
            os.makedirs(ffmpeg_dir)
        extract_ffmpeg(ffmpeg_zip, ffmpeg_dir)
        ffmpeg_bin = None
        if os.path.isdir(ffmpeg_dir):
            for name in os.listdir(ffmpeg_dir):
                exe = os.path.join(ffmpeg_dir, name, "bin", "ffmpeg.exe")
                if os.path.isfile(exe):
                    ffmpeg_bin = os.path.join(ffmpeg_dir, name, "bin")
                    break

        if ffmpeg_bin is None:
            raise FileNotFoundError("ffmpeg.exe not found under Program Files\\ffmpeg")

        with reg.OpenKey(
            reg.HKEY_CURRENT_USER,
            r"Environment",
            0,
            reg.KEY_READ | reg.KEY_WRITE
        ) as key:
            try:
                current_path, _ = reg.QueryValueEx(key, "PATH")
            except FileNotFoundError:
                current_path = ""

            paths = current_path.split(";") if current_path else []

            if ffmpeg_bin not in paths:
                new_path = current_path + (";" if current_path else "") + ffmpeg_bin
                reg.SetValueEx(
                    key,
                    "PATH",
                    0,
                    reg.REG_EXPAND_SZ,
                    new_path
                )
    print("FFmpeg nainstalovany")

    try:
        subprocess.check_output(["nvcc", "--version"])
        print("CUDA nainstalovane")
    except:
        choice = input("CUDA is required for GPU acceleration. Install now? (y/n): ").strip().lower()
        if choice == "y":
            print("Stahujem CUDA")
            cuda_url = "https://developer.download.nvidia.com/compute/cuda/13.1.0/local_installers/cuda_13.1.0_windows.exe"
            cuda_installer = os.path.join(os.environ["TEMP"], "cuda_installer.exe")
            download_file(cuda_url, cuda_installer)
            run_installer(cuda_installer)
            print("CUDA stiahnute")
        else:
            print("CUDA instalacia preskocena")
    input("")
if __name__ == "__main__":
    main()
