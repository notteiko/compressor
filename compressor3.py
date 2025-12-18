try:
    import PyQt6
except:
    import os
    os.system("pip install pyqt6")
import subprocess
import winreg as reg
import urllib.request
import zipfile
import ctypes
import sys
import re
import os
from time import sleep
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout,QHBoxLayout, QSlider, QStyle, QTextEdit, QLabel, QComboBox, QGraphicsOpacityEffect, QMessageBox, QProgressBar, QCheckBox, QSizePolicy
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl, Qt, QProcess, QMimeData
from PyQt6.QtGui import QPixmap, QColor, QFont

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

def install():
    if not is_admin():
        print("Re-launching as administrator...")
        relaunch_as_admin()
    app_folder = os.path.join(os.environ["LOCALAPPDATA"], "Compressor")
    os.makedirs(app_folder, exist_ok=True)
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

def get_framerate(video_path):
    cmd = [
        "ffprobe",
        "-v", "0",
        "-of", "csv=p=0",
        "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate",
        video_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
    rate = result.stdout.strip()
    if "/" in rate:
        num, denom = rate.split("/")
        return str(float(num) / float(denom))
    return str(float(rate))

def get_framecount(video_path):
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-count_packets",
        "-show_entries","stream=nb_read_packets",
        "-of", "csv=p=0",
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
    return result.stdout.strip()

def get_bitrate(video_path):
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=bit_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
    return int(result.stdout.strip())

class ClickableSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Calculate the value where you clicked
            if self.orientation() == Qt.Orientation.Horizontal:
                new_val = round((event.position().x() / self.width()) * (self.maximum() - self.minimum()) + self.minimum())
            else:
                new_val = round((event.position().y() / self.height()) * (self.maximum() - self.minimum()) + self.minimum())
            self.setValue(new_val)
            # Emit sliderMoved to trigger seeking
            self.sliderMoved.emit(new_val)
        super().mousePressEvent(event)


class VideoPlayer(QWidget):
    def __init__(self):
        super().__init__()

        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.on_stdout)
        self.process.readyReadStandardError.connect(self.on_stderr)
        self.process.finished.connect(self.onProcessFinished)

        self.enterCounter = 0
        self.player = QMediaPlayer()
        self.audio = QAudioOutput()
        self.player.setAudioOutput(self.audio)

        self.video_widget = QVideoWidget()
        self.player.setVideoOutput(self.video_widget)

        self.play_btn = QPushButton()
        self.icon_play = app.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        self.play_btn.setIcon(self.icon_play)
        self.play_btn.clicked.connect(self.toggle_play)

        top_controls = QHBoxLayout()
        top_controls.addWidget(self.play_btn)

        # Three extra buttons
        self.btn1 = QPushButton("<<")
        self.btn2 = QPushButton(">>")

        bottom_controls = QHBoxLayout()
        bottom_controls.addWidget(self.btn1)
        bottom_controls.addWidget(self.btn2)

        layout = QVBoxLayout()  # main vertical layout
        layout.addWidget(self.video_widget, stretch=1)

        self.cas_layout = QHBoxLayout()
        self.time_label = QLabel("00:00.000")
        self.player.positionChanged.connect(self.update_time)
        self.cas_layout.addWidget(self.time_label, alignment=Qt.AlignmentFlag.AlignLeft)

        self.time_label_koniec = QLabel()
        self.player.durationChanged.connect(self.update_total_time)
        self.cas_layout.addWidget(self.time_label_koniec, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout.addLayout(self.cas_layout)

        # Slider below video
        self.slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.seek)
        self.player.positionChanged.connect(self.update_slider)
        self.player.durationChanged.connect(self.update_duration)

        layout.addWidget(self.slider)

        self.prvy_point = QLabel(self)
        pix = QPixmap(r"E:\Users\Teiko\Downloads\ofsdksdfo.png")
        self.prvy_point.setPixmap(pix.scaled(20,30))
        self.prvy_point.hide()

        self.druhy_point = QLabel(self)
        pix = QPixmap(r"E:\Users\Teiko\Downloads\ofsdksdfo.png")
        self.druhy_point.setPixmap(pix.scaled(20,30))
        self.druhy_point.hide()
        
        self.rect_widget = QWidget(self)
        self.rect_widget.setStyleSheet("background-color: red;")
        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(0.2)
        self.rect_widget.hide()
        self.rect_widget.setGraphicsEffect(opacity_effect)
        # Horizontal layout for buttons below slider
        controls = QHBoxLayout()
        controls.addWidget(self.btn1)
        controls.addWidget(self.play_btn)
        controls.addWidget(self.btn2)

        layout.addLayout(controls)
        self.file = sys.argv[1]

        layout_pod_playerom = QHBoxLayout()

        self.text_random = QLabel("V3-dev")
        layout_pod_playerom.addWidget(self.text_random, alignment=Qt.AlignmentFlag.AlignLeft)

        self.cuda_text = QLabel("")
        layout_pod_playerom.addWidget(self.cuda_text, alignment=Qt.AlignmentFlag.AlignCenter)

        self.fps = get_framerate(self.file)
        self.fps_text = QLabel("FPS: " + self.fps)
        layout_pod_playerom.addWidget(self.fps_text, alignment=Qt.AlignmentFlag.AlignRight)

        total_ms = self.player.duration()
        minutes = total_ms // 60000
        seconds = (total_ms % 60000) // 1000
        milliseconds = total_ms % 1000
        formatted = f"{minutes:02}:{seconds:02}.{milliseconds:03}"
        self.time_label_koniec.setText(formatted)

        layout.addLayout(layout_pod_playerom)
        layout2 = QVBoxLayout()

        self.compress_layout = QHBoxLayout()
        self.tlacitko_compress = QCheckBox("Compress to")
        self.tlacitko_compress.setChecked(True)
        self.size_moznosti = QTextEdit()
        self.size_moznosti.setMaximumSize(56,28)
        self.size_moznosti.setPlainText("10")
        self.compress_layout.addWidget(self.tlacitko_compress)
        self.compress_layout.addWidget(self.size_moznosti, alignment=Qt.AlignmentFlag.AlignLeft)
        self.mb_label = QLabel("MB")
        self.compress_layout.addWidget(self.mb_label)

        self.textedit_compress_layout = QHBoxLayout()
        self.textedit_compress = QTextEdit()
        #self.textedit_compress_layout.addWidget(self.textedit_compress)
        self.textedit_compress.hide()
        self.textedit_compress.setMaximumSize(80, 30)

        self.resolution_layout = QHBoxLayout()
        self.tlacitko_resolution = QCheckBox("Resolution")
        self.resolution_moznosti = QTextEdit()
        self.resolution_layout.addWidget(self.tlacitko_resolution)
        self.resolution_layout.addWidget(self.resolution_moznosti)
        self.resolution_moznosti.setMaximumSize(108,28)
        self.resolution_moznosti.setPlainText("1920x1080")

        self.casovy_usek = QLabel("00:00.000-00:00.000")
        self.casovy_usek_total_cas = QLabel("")
        self.casovy_usek.hide()
        self.casovy_usek_total_cas.hide()
        
        self.render_progress_text = QLabel("0%")
        self.render_progress_text.setStyleSheet("font-size: 20pt;")
        self.render_progress_text.hide()

        self.render_progress = QProgressBar()
        self.render_progress.setRange(0,0)
        self.render_progress.setFixedSize(180,20)
        self.render_progress.setTextVisible(False)
        self.render_progress.hide()

        self.startTlacitko = QPushButton("OZNAČ ČASŤ VIDEA")
        self.startTlacitko.setStyleSheet("background-color: #570000;")
        self.startTlacitko.setMinimumHeight(50)
        self.startTlacitko_wrapper = QVBoxLayout()
        self.startTlacitko_wrapper.addWidget(self.casovy_usek, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, stretch=1)
        self.startTlacitko_wrapper.addWidget(self.casovy_usek_total_cas, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter)
        self.startTlacitko_wrapper.addWidget(self.render_progress_text, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter)
        self.startTlacitko_wrapper.addWidget(self.render_progress, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter)
        self.startTlacitko_wrapper.addWidget(self.startTlacitko, alignment=Qt.AlignmentFlag.AlignBottom)
        self.startTlacitko_wrapper.setContentsMargins(0,0,0,10)

        # --- Volume layout ---
        self.volume_layout = QHBoxLayout()

        self.volume_icon_label = QLabel()
        self.volume_icon_pix = QPixmap(r"E:\Users\Teiko\Downloads\minimal-speaker-icon.png")
        self.scaled = self.volume_icon_pix.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio)
        self.volume_icon_label.setPixmap(self.scaled)
        self.volume_icon_label.setFixedSize(20, 20)

        # Add icon (no stretch)
        self.volume_layout.addWidget(self.volume_icon_label, alignment=Qt.AlignmentFlag.AlignBottom)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.audio.setVolume(50 / 100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.volume_layout.addWidget(self.volume_slider, alignment=Qt.AlignmentFlag.AlignBottom)
        self.volume_wrapper = QHBoxLayout()
        self.volume_wrapper.addLayout(self.volume_layout)
    
        layout2.addLayout(self.compress_layout)
        layout2.addWidget(self.textedit_compress, alignment=Qt.AlignmentFlag.AlignRight)
        layout2.addLayout(self.resolution_layout)
        layout2.addLayout(self.startTlacitko_wrapper, stretch=1)
        layout2.addLayout(self.volume_wrapper)
        layout2.setContentsMargins(10,10,10,0)

        celegui = QHBoxLayout()
        celegui.addLayout(layout, 1)
        celegui.addLayout(layout2)

        self.setLayout(celegui)

        self.setWindowTitle("Compressor")
        self.player.setSource(QUrl.fromLocalFile(self.file))
        self.player.play()
        self.player.pause()
        
        try:
            cuda_output = subprocess.check_output(["nvcc", "--version"], creationflags=subprocess.CREATE_NO_WINDOW).decode()
            self.cuda_text.setText(cuda_output.replace("\n", "").split(" ")[-1])
        except Exception:
            self.cuda_text.setText("bez CUDA podpory, nainstaluj pre HW render")

    def toggle_play(self):
        self.icon_play = app.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
        self.icon_pause = app.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause)
        if self.player.isPlaying():
            self.play_btn.setIcon(self.icon_play)
            self.player.pause()
        else:
            self.play_btn.setIcon(self.icon_pause)
            self.player.play()

    def set_volume(self, value):
        self.audio.setVolume(value / 100)

    def update_slider(self, pos):
        self.slider.setValue(pos)

    def update_duration(self, dur):
        self.slider.setRange(0, dur)

    def seek(self, pos):
        self.player.setPosition(pos)
    
    def update_time(self, pos):
        self.total_ms = pos
        minutes = self.total_ms // 60000
        seconds = (self.total_ms % 60000) // 1000
        milliseconds = self.total_ms % 1000
        self.time_label.setText(f"{minutes:02}:{seconds:02}.{milliseconds:03}")

    def update_total_time(self, dur):
        self.time_label_koniec.setText(
            f"{dur // 60000:02}:{(dur % 60000) // 1000:02}.{dur % 1000:03}"
        )

    def on_stdout(self):
        pass

    def on_stderr(self):
        output = bytes(self.process.readAllStandardError()).decode(errors="ignore")
        if (frame_match := re.search(r"frame=\s*(\d+)", output)):
            self.frame = int(frame_match.group(1))
            segment_ms = self.druhy_point_cas - self.prvy_point_cas
            segment_s = segment_ms / 1000
            fps = float(self.fps)  # frames per second
            segment_frames = segment_s * fps
            percent = (self.frame / segment_frames) * 100
            self.render_progress.setRange(0,100)
            self.render_progress.setValue(round(percent))
            print(f"{round(percent)}%")
            self.render_progress_text.setText(f"{round(percent)}%")
            self.render_progress_text.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return:
            handle_width = self.slider.style().pixelMetric(self.slider.style().PixelMetric.PM_SliderLength)
            slider_width = self.slider.width()
            slider_height = self.slider.height()
            usable_width = slider_width - handle_width
            val = self.slider.value()
            min_val = self.slider.minimum()
            max_val = self.slider.maximum()
            handle_x = int((val - min_val) / (max_val - min_val) * usable_width)
            handle_x += (handle_width // 2) + 2
            self.total_ms = getattr(self, 'total_ms', 0)
            minutes = self.total_ms // 60000
            seconds = (self.total_ms % 60000) // 1000
            milliseconds = self.total_ms % 1000
            self.casovy_usek.show()
            if self.enterCounter == 0:
                self.prvy_point.setGeometry(handle_x, 397, 20, 30)
                self.prvy_point.show()
                self.prvy_point_cas = self.slider.value()
                self.casovy_usek.setText(f"{minutes:02}:{seconds:02}.{milliseconds:03} - ")
                print(self.total_ms)
            elif self.enterCounter == 1:
                self.druhy_point.setGeometry(handle_x, 397, 20, 30)
                self.druhy_point.show()
                self.casovy_usek_total_cas.show()
                self.druhy_point_cas = self.slider.value()
                self.rect_widget.setGeometry(self.prvy_point.x()+10, 405, self.druhy_point.x()-self.prvy_point.x(), 20)  # x, y, width, height
                self.rect_widget.show()
                self.casovy_usek.setText(self.casovy_usek.text() + f"{minutes:02}:{seconds:02}.{milliseconds:03}")
                self.casovy_usek_total_cas.show()
                self.casovy_usek_total_cas.setText(str(round(((self.druhy_point_cas - self.prvy_point_cas)/1000), 1)) + "s")
                print(self.total_ms)
                self.startTlacitko.clicked.connect(self.start)
                self.startTlacitko.setStyleSheet(f"background-color: #0094d4;")
                self.startTlacitko.setText("ŠTART (ENTER)")
            elif self.enterCounter == 2:
                self.start()
            self.enterCounter += 1

    def start(self):
        self.render_progress.show()
        command = f'ffmpeg -y -hwaccel cuda -i "{self.file}"'
        command = command + f" -ss {self.prvy_point_cas/1000} -to {self.druhy_point_cas/1000}"
        self.path_trimmed = self.file[:-4]
        if self.tlacitko_compress.isChecked():
            self.bitrate = int(int(self.size_moznosti.toPlainText()) * 1024 * 8 / ((self.druhy_point_cas - self.prvy_point_cas) / 1000))
            command = command + f" -b:v {self.bitrate}k -bufsize {self.bitrate}k -maxrate {self.bitrate}k"
        command = command + f' "{self.path_trimmed}_compressed.mp4"'
        print(command)
        self.process.start(command)

    def onProcessFinished(self):
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(f"{self.path_trimmed}_compressed.mp4")])
        QApplication.clipboard().setMimeData(mime)
        self.render_progress_text.setStyleSheet("font-size: 16pt;")
        self.render_progress_text.setText("Skopírované!")
        self.startTlacitko.clicked.connect(self.openDone)
        self.startTlacitko.setText("OTVOR PRIEČINOK")
    
    def openDone(self):
        os.popen(f'explorer /select,"{self.path_trimmed}_compressed.mp4"')
    
if __name__ == "__main__":
    try:
        sys.argv[1]
        app = QApplication(sys.argv)
        player = VideoPlayer()
        player.resize(800, 500)
        player.show()
    except:
        install()
    sys.exit(app.exec())