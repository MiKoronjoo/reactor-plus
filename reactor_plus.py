import dataclasses

import cv2
from PyQt5 import QtCore, QtGui, QtWidgets


def size(value: int):
    return round(value * RESIZE) or 1


def video_pixmap(video_path: str):
    video = cv2.VideoCapture(video_path)
    pixmap = None
    success, frame = video.read()
    if success:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        q_image = QtGui.QImage(frame.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(q_image)
    video.release()
    return pixmap


RESIZE = 2


class FileFilter:
    IMAGES = 'Image files (*.png *.jpg *.jpeg *.bmp)'
    VIDEOS = 'Video files (*.mp4 *.mkv *.avi *.mov *.wmv)'


@dataclasses.dataclass
class Data:
    face_file_paths: list[str] = None
    target_file_paths: list[str] = None
    is_target_video: bool = False
    operation: str = 'both'
    keep_fps: bool = True
    keep_audio: bool = True
    keep_frames: bool = False


class ClickableLabel(QtWidgets.QLabel):
    left_clicked = QtCore.pyqtSignal()
    right_clicked = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.left_clicked.emit()
        else:
            self.right_clicked.emit()


class MainWindow(QtWidgets.QMainWindow):
    resized = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("window_main")
        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        self.button_select_face = QtWidgets.QPushButton(self.centralwidget)
        self.button_select_face.setObjectName("button_select_face")
        self.button_select_target = QtWidgets.QPushButton(self.centralwidget)
        self.button_select_target.setObjectName("button_select_target")
        self.button_start = QtWidgets.QPushButton(self.centralwidget)
        self.button_start.setObjectName("button_start")
        self.button_preview = QtWidgets.QPushButton(self.centralwidget)
        self.button_preview.setObjectName("button_preview")
        self.checkbox_fps = QtWidgets.QCheckBox(self.centralwidget)
        self.checkbox_fps.setObjectName("checkbox_fps")
        self.checkbox_frames = QtWidgets.QCheckBox(self.centralwidget)
        self.checkbox_frames.setObjectName("checkbox_frames")
        self.checkbox_audio = QtWidgets.QCheckBox(self.centralwidget)
        self.checkbox_audio.setObjectName("checkbox_audio")
        self.radio_both = QtWidgets.QRadioButton(self.centralwidget)
        self.radio_both.setObjectName("radio_both")
        self.radio_swap = QtWidgets.QRadioButton(self.centralwidget)
        self.radio_swap.setObjectName("radio_swap")
        self.radio_enhance = QtWidgets.QRadioButton(self.centralwidget)
        self.radio_enhance.setObjectName("radio_enhance")
        self.image_face = ClickableLabel(self.centralwidget)
        self.image_face.setObjectName("image_face")
        self.image_target = ClickableLabel(self.centralwidget)
        self.image_target.setObjectName("image_target")
        self.progress_bar = QtWidgets.QProgressBar(self.centralwidget)
        self.progress_bar.setObjectName("progress_bar")
        self.label_main = QtWidgets.QLabel(self.centralwidget)
        self.label_main.setObjectName("label_main")
        self.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)

        self.cache = {}
        self.data = Data()

        self.setup_ui()
        self.set_defaults()
        self.retranslate_ui()
        self.setup_connections()

        QtCore.QMetaObject.connectSlotsByName(self)

    def set_defaults(self):
        self.checkbox_fps.setChecked(self.data.keep_fps)
        self.checkbox_audio.setChecked(self.data.keep_audio)
        self.radio_both.setChecked(True)
        self.image_face.setPixmap(QtGui.QPixmap(self.data.face_file_paths))
        self.image_face.setScaledContents(True)
        self.image_target.setPixmap(QtGui.QPixmap(self.data.target_file_paths))
        self.image_target.setScaledContents(True)
        self.progress_bar.setProperty("value", 0)
        self.progress_bar.setAlignment(QtCore.Qt.AlignCenter)
        self.label_main.setAlignment(QtCore.Qt.AlignCenter)

    def setup_ui(self):
        self.resize(size(600), size(700))
        # self.setFixedSize(size(600), size(700))
        self.button_select_face.setGeometry(QtCore.QRect(size(90), size(280), size(141), size(41)))
        self.button_select_target.setGeometry(QtCore.QRect(size(370), size(280), size(141), size(41)))
        self.button_start.setGeometry(QtCore.QRect(size(120), size(490), size(81), size(31)))
        self.button_preview.setGeometry(QtCore.QRect(size(400), size(490), size(81), size(31)))
        self.checkbox_fps.setGeometry(QtCore.QRect(size(360), size(380), size(161), size(16)))
        self.checkbox_frames.setGeometry(QtCore.QRect(size(360), size(440), size(161), size(16)))
        self.checkbox_audio.setGeometry(QtCore.QRect(size(360), size(410), size(161), size(16)))
        self.radio_both.setGeometry(QtCore.QRect(size(80), size(380), size(161), size(16)))
        self.radio_swap.setGeometry(QtCore.QRect(size(80), size(410), size(161), size(16)))
        self.radio_enhance.setGeometry(QtCore.QRect(size(80), size(440), size(161), size(16)))
        self.image_face.setGeometry(QtCore.QRect(size(60), size(50), size(201), size(201)))
        self.image_target.setGeometry(QtCore.QRect(size(340), size(50), size(201), size(201)))
        self.progress_bar.setGeometry(QtCore.QRect(size(40), size(630), size(521), size(23)))
        self.label_main.setGeometry(QtCore.QRect(size(40), size(560), size(521), size(61)))
        self.setStyleSheet("#window_main {\n"
                           "background-color: rgb(0, 25, 25);\n"
                           "}\n"
                           "QRadioButton {\n"
                           f"font: {size(6)}pt \"Arial\";\n"
                           "color: #ffffff;\n"
                           "}\n"
                           "QRadioButton::indicator {\n"
                           f"width: {size(14)}px;\n"
                           f"height: {size(14)}px;\n"
                           "}\n"
                           "QRadioButton::hover {\n"
                           "color: #66ffae;\n"
                           "}\n"
                           "QRadioButton::indicator::unchecked {\n"
                           "image: url(images/off-radio-button.png);\n"
                           "}\n"
                           "QRadioButton::indicator::checked {\n"
                           "image: url(images/on-radio-button.png);\n"
                           "}\n"
                           "QCheckBox {\n"
                           f"font: {size(6)}pt \"Arial\";\n"
                           "color: #ffffff;\n"
                           "}\n"
                           "QCheckBox::indicator {\n"
                           f"width: {size(25)}px;\n"
                           f"height: {size(25)}px;\n"
                           "}\n"
                           "QCheckBox::hover {\n"
                           "color: #66ffae;\n"
                           "}\n"
                           "QCheckBox::indicator::unchecked {\n"
                           "image: url(images/off-button.png);\n"
                           "}\n"
                           "QCheckBox::indicator::checked {\n"
                           "image: url(images/on-button.png);\n"
                           "}\n"
                           "QPushButton {\n"
                           "border:none;\n"
                           "color:black;\n"
                           "background-color:#00ad7c;\n"
                           f"font: {size(7)}pt \"Arial\";\n"
                           f"border-radius:{size(2)}px;\n"
                           "}\n"
                           "QPushButton::hover {\n"
                           "background-color:#00835c;\n"
                           "}\n"
                           "QPushButton::pressed {\n"
                           "background-color:qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #00938e, stop:1 #00835c);\n"
                           "}\n")
        self.progress_bar.setStyleSheet("QProgressBar {\n"
                                        f"    font: {size(7)}pt \"Arial\";\n"
                                        "}")
        self.label_main.setStyleSheet(f"font: {size(8)}pt \"Arial\";\n"
                                      "color: #ffffff;")

    def retranslate_ui(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("window_main", "MainWindow"))
        self.button_select_face.setText(_translate("window_main", "Select face"))
        self.button_select_target.setText(_translate("window_main", "Select target"))
        self.button_start.setText(_translate("window_main", "Start"))
        self.button_preview.setText(_translate("window_main", "Preview"))
        self.checkbox_fps.setText(_translate("window_main", "Keep FPS"))
        self.checkbox_frames.setText(_translate("window_main", "Keep extracted frames"))
        self.checkbox_audio.setText(_translate("window_main", "Keep audio"))
        self.radio_both.setText(_translate("window_main", "Swap and Enhance face"))
        self.radio_swap.setText(_translate("window_main", "only Swap face"))
        self.radio_enhance.setText(_translate("window_main", "only Enhance face"))
        self.label_main.setText(_translate("window_main", "Processing..."))

    def setup_connections(self):
        self.button_select_face.clicked.connect(self.select_face)
        self.button_select_target.clicked.connect(self.select_target)

        self.image_face.left_clicked.connect(self.next_face_image)
        self.image_target.left_clicked.connect(self.next_target_image)
        self.image_face.right_clicked.connect(self.prev_face_image)
        self.image_target.right_clicked.connect(self.prev_target_image)

        self.resized.connect(self.handle_resize)

    def next_face_image(self):
        if self.data.face_file_paths:
            self.data.face_file_paths.append(self.data.face_file_paths.pop(0))
            self.image_face.setPixmap(QtGui.QPixmap(self.data.face_file_paths[0]))

    def next_target_image(self):
        if self.data.target_file_paths:
            self.data.target_file_paths.append(self.data.target_file_paths.pop(0))
            self._set_target_image()

    def prev_face_image(self):
        if self.data.face_file_paths:
            self.data.face_file_paths.insert(0, self.data.face_file_paths.pop())
            self.image_face.setPixmap(QtGui.QPixmap(self.data.face_file_paths[0]))

    def prev_target_image(self):
        if self.data.target_file_paths:
            self.data.target_file_paths.insert(0, self.data.target_file_paths.pop())
            self._set_target_image()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resized.emit()

    def handle_resize(self):
        w = self.width() / 600
        h = self.height() / 700
        global RESIZE
        RESIZE = min(w, h)
        self.setup_ui()

    def select_face(self):
        paths, _ = self.open_file_dialog([FileFilter.IMAGES])
        if not paths:
            return
        self.data.face_file_paths = paths
        self.image_face.setPixmap(QtGui.QPixmap(self.data.face_file_paths[0]))

    def select_target(self):
        paths, _filter = self.open_file_dialog([FileFilter.IMAGES, FileFilter.VIDEOS])
        if not paths:
            return
        self.data.target_file_paths = paths
        self.data.is_target_video = _filter == FileFilter.VIDEOS
        if self.data.is_target_video:
            for path in paths:
                self.cache[path] = video_pixmap(path)
        self._set_target_image()

    def _set_target_image(self):
        if self.data.is_target_video:
            pixmap = self.cache.get(self.data.target_file_paths[0])
        else:
            pixmap = QtGui.QPixmap(self.data.target_file_paths[0])
        self.image_target.setPixmap(pixmap)

    def open_file_dialog(self, file_filters: list = None):
        if file_filters is None:
            _filter = ''
        else:
            _filter = ';;'.join(file_filters)
        return QtWidgets.QFileDialog.getOpenFileNames(self, 'Open file', '', _filter)


def lunch_app():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    lunch_app()
