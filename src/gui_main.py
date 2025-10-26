# gui_main.py
import sys
import os
import re
import subprocess
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QCheckBox,
    QPushButton, QTextEdit, QFormLayout, QVBoxLayout,
    QMessageBox, QFrame
)

# ANSI escape 제거용 정규식
ANSI_ESCAPE = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

class ProcessWorker(QThread):
    # (출력 텍스트, is_progress_flag)
    line_signal     = pyqtSignal(str, bool)
    puth_signal     = pyqtSignal()
    finished_signal = pyqtSignal()

    def __init__(self, cmd, cwd):
        super().__init__()
        self.cmd = cmd    # 호출할 커맨드 리스트
        self.cwd = cwd
        self.proc = None

    def run(self):
        try:
            self.proc = subprocess.Popen(
                self.cmd,
                cwd=self.cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        except Exception as e:
            # 실행 실패시 로그에 에러 텍스트로 보여주고 종료
            self.line_signal.emit(f"프로세스 실행 실패: {e}", False)
            self.finished_signal.emit()
            return

        buf = ""
        while True:
            ch = self.proc.stdout.read(1)
            if not ch:
                break
            # carriage return: 덮어쓰기 표시
            if ch == "\r":
                line = ANSI_ESCAPE.sub("", buf)
                buf = ""
                self.line_signal.emit(line, True)
            # newline: 줄바꿈
            elif ch == "\n":
                line = ANSI_ESCAPE.sub("", buf)
                buf = ""
                is_prog = "%|" in line  # tqdm 진행줄 판단
                self.line_signal.emit(line, is_prog)
                if "puth the streaming button" in line:
                    self.puth_signal.emit()
            else:
                buf += ch

        # 남은 버퍼 처리
        if buf:
            line = ANSI_ESCAPE.sub("", buf)
            self.line_signal.emit(line, False)

        self.proc.wait()
        self.finished_signal.emit()

    def stop(self):
        if self.proc and self.proc.poll() is None:
            try:
                subprocess.call(
                    ["taskkill", "/F", "/T", "/PID", str(self.proc.pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except:
                pass
            self.proc = None

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.setWindowTitle("YOLO Streaming Launcher")
        self.resize(600, 550)
        self._build_ui()

    def _build_ui(self):
        form = QFormLayout()
        self.model_edit   = QLineEdit("yolo11x")
        self.stream_edit  = QLineEdit("rtsp://192.168.0.2:8554/")
        self.test_mode_cb = QCheckBox()
        self.fps_edit     = QLineEdit("10")
        self.pc_fps_edit  = QLineEdit("30")
        self.skip_edit    = QLineEdit("30")
        form.addRow("YOLO 모델:", self.model_edit)
        form.addRow("Stream URL:", self.stream_edit)
        form.addRow("Test Mode:", self.test_mode_cb)
        form.addRow("Target FPS:", self.fps_edit)
        form.addRow("PeopleCounting FPS:", self.pc_fps_edit)
        form.addRow("Skip Time (s):", self.skip_edit)

        self.run_btn = QPushButton("실행")
        self.run_btn.clicked.connect(self.run_main)

        self.reminder = QLabel("")
        self.reminder.setAlignment(Qt.AlignCenter)
        self.reminder.setStyleSheet("font-size:18pt; font-weight:bold; color:red;")
        self.reminder.setVisible(False)

        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Sunken)
        self.separator.setVisible(False)
        self.separator.setLineWidth(1)

        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("font-family:monospace;")

        self.log = QTextEdit()
        self.log.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.run_btn)
        layout.addWidget(self.reminder)
        layout.addWidget(self.separator)
        layout.addSpacing(5)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.log)

    def run_main(self):
        # 이미 실행 중이면 종료
        if self.worker:
            self.worker.stop()
            self.worker.wait()

        # UI 초기화
        self.log.clear()
        self.reminder.setVisible(False)
        self.separator.setVisible(False)
        self.progress_label.clear()
        self.run_btn.setEnabled(False)

        # exe 모드인지 스크립트 모드인지에 따라 base_dir 결정
        if getattr(sys, "frozen", False):
            # PyInstaller onedir 빌드: exe 위치 기준
            base_dir = os.path.dirname(sys.executable)
            python_exec = sys.executable
        else:
            # 스크립트 모드: 현재 파일 위치 기준
            base_dir = os.path.dirname(os.path.abspath(__file__))
            python_exec = sys.executable

        # main.py 경로
        main_py = os.path.join(base_dir, "main.py")
        if not os.path.exists(main_py):
            QMessageBox.critical(self, "오류", f"main.py를 찾을 수 없습니다:\n{main_py}")
            self.run_btn.setEnabled(True)
            return

        # subprocess 호출 커맨드 조립
        cmd = [
            python_exec, "-u", main_py,
            "--yolo_model", self.model_edit.text(),
            "--stream_url", self.stream_edit.text(),
            "--target_fps", self.fps_edit.text(),
            "--target_fps_PeopleCounting", self.pc_fps_edit.text(),
            "--skip_time", self.skip_edit.text()
        ]
        if self.test_mode_cb.isChecked():
            cmd += ["--test_mode", "True"]

        # 로그에 보여주기
        self.log.append(f"▷ 실행: {' '.join(cmd)}\n")

        # 백그라운드 프로세스 시작
        self.worker = ProcessWorker(cmd, base_dir)
        self.worker.line_signal.connect(self._handle_line)
        self.worker.puth_signal.connect(self._show_reminder)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

    def _handle_line(self, line, is_progress):
        if not line.strip():
            return
        if is_progress:
            self.progress_label.setText(line)
        else:
            self.log.append(line)

    def _show_reminder(self):
        self.reminder.setText("▶ Video Load 버튼을 눌러주세요.")
        self.reminder.setVisible(True)
        self.separator.setVisible(True)

    def _on_finished(self):
        self.run_btn.setEnabled(True)
        QMessageBox.information(self, "완료", "Done")

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
