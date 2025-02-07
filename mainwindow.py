"""functions of the UI"""

import os

# -------------------- Import Lib Tier -------------------
from PyQt5.QtWidgets import QMainWindow, QFileDialog
from PyQt5.QtCore import QObject, QDir, pyqtSlot, pyqtSignal, QThread

# -------------------- Import Lib User -------------------
from Ui_mainwindow import Ui_MainWindow
from api import steam_game_api
from api import xdelta_api
import debug

PATH_PATCH = ".\\patch\\"
GAME_FOLDER_NAME = "Zero Escape The Nonary Games"


# -------------------------------------------------------------------#
#                          CLASS WORKER                              #
# -------------------------------------------------------------------#
class _Worker(QObject):

    signal_apply_patch = pyqtSignal(str)
    signal_set_text_progress = pyqtSignal(str)
    signal_apply_patch_end = pyqtSignal(str)

    choice_patch_launcher = True
    choice_patch_999 = True
    choice_patch_vlr = True

    def __init__(self) -> None:
        super().__init__()

    def set_text_progress(self, text):
        self.signal_set_text_progress.emit(text)

    def error_management(self, error: str) -> None:
        debug.logging.error(error)
        self.set_text_progress(error)

    def is_folder_patch_exists(self) -> bool:
        return os.path.exists(PATH_PATCH)

    def apply_patch_by_name(self, gamepath: str, patch_name: str) -> None:
        self.set_text_progress("Application du patch de " + patch_name + " en cours")
        file_to_patch: str = os.path.join(gamepath, patch_name)
        patch_file: str = os.path.join(PATH_PATCH, patch_name + ".xdelta")
        res = xdelta_api.apply_patch(file_to_patch, patch_file)
        if res != 0:
            if res == -4:
                self.error_management("le fichier " + patch_name + " n'est pas celui d'origine ou il est déjà patché")
            else:
                self.error_management("erreur " + str(res) + " lors de l'application du patch de " + patch_name)
            return
        self.set_text_progress("Application du patch de " + patch_name + " terminée")

    def apply_patch_launcher(self, gamepath: str) -> None:
        new_launcher_patch_name: str = "Launcher.exe"
        old_launcher_patch_name: str = "Launcher.exe_999_already"

        self.set_text_progress("Application du patch de Launcher.exe en cours")
        file_to_patch: str = os.path.join(gamepath, new_launcher_patch_name)
        patch_file: str = os.path.join(PATH_PATCH, new_launcher_patch_name + ".xdelta")
        res = xdelta_api.apply_patch(file_to_patch, patch_file)
        if res != 0:
            patch_file: str = os.path.join(PATH_PATCH, old_launcher_patch_name + ".xdelta")
            res = xdelta_api.apply_patch(file_to_patch, patch_file)
            if res != 0:
                if res == -4:
                    self.error_management("le fichier " + new_launcher_patch_name + " n'est pas celui d'origine ou il est déjà patché")
                else:
                    self.error_management(
                        "erreur " + str(res) + " lors de l'application du patch de " + new_launcher_patch_name
                    )
                return
        self.set_text_progress("Application du patch de " + new_launcher_patch_name + " terminée")

    def apply_patch_process(self, gamepath: str) -> None:

        if xdelta_api.define_xdelta_path("xdelta") == -1:
            self.error_management("xdelta3.exe non trouvé ou dossier xdelta n'existe pas")
            self.signal_apply_patch_end.emit("processus terminé")
            return
        if not self.is_folder_patch_exists():
            self.error_management("dossier 'patch' non présent")
            self.signal_apply_patch_end.emit("processus terminé")
            return

        if self.choice_patch_launcher:
            self.apply_patch_launcher(gamepath)
        if self.choice_patch_999:
            self.apply_patch_by_name(gamepath, "ze1.exe")
            self.apply_patch_by_name(gamepath, "ze1_data.bin")
        if self.choice_patch_vlr:
            self.apply_patch_by_name(gamepath, "ze2_data_en_us.bin")

        self.signal_apply_patch_end.emit("Fin de l'application des patchs")


# -------------------------------------------------------------------#
#                         CLASS MAINWINDOW                           #
# -------------------------------------------------------------------#
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.m_thread = QThread()
        self.m_thread.start()
        self.m_worker = _Worker()
        self.m_worker.moveToThread(self.m_thread)

        self.set_up_connect()

        self.find_steam_game_path()

    def set_up_connect(self) -> None:
        self.m_worker.signal_apply_patch.connect(self.m_worker.apply_patch_process)
        # Buttons
        self.ui.pushButton_browse.clicked.connect(self.find_element)
        self.ui.pushButton_process.clicked.connect(self.run_process)
        # CheckBoxes
        self.ui.checkBox_Launcher.clicked.connect(self.update_checkbox_launcher)
        self.ui.checkBox_999.clicked.connect(self.update_checkbox_999)
        self.ui.checkBox_VLR.clicked.connect(self.update_checkbox_vlr)
        # worker
        self.m_worker.signal_apply_patch_end.connect(self.handle_apply_patch_result)
        self.ui.lineEdit_gamePath.textChanged.connect(self.on_game_path_changed)
        self.m_worker.signal_set_text_progress.connect(self.change_progress_text)

    def find_steam_game_path(self) -> None:
        gamepath: str | int = steam_game_api.find_game_path(GAME_FOLDER_NAME)
        if isinstance(gamepath, str):
            self.ui.lineEdit_gamePath.setText(gamepath)
        else:
            self.ui.pushButton_process.setEnabled(False)
            debug.logging.info("probleme avec find_game_path, error : " + str(gamepath))

    @pyqtSlot()
    def find_element(self) -> None:
        """open the finder windows,
        put the path in the fileEdit
        """
        folder: str = QFileDialog.getExistingDirectory(self, "Choisir dossier jeu steam",
                                                       QDir.currentPath(), QFileDialog.ShowDirsOnly)
        self.ui.lineEdit_gamePath.setText(folder)
        if len(self.ui.lineEdit_gamePath.text()) == 0 or not os.path.exists(self.ui.lineEdit_gamePath.text()):
            self.ui.pushButton_process.setEnabled(False)
        else:
            self.ui.pushButton_process.setEnabled(True)

    @pyqtSlot(str)
    def on_game_path_changed(self, new_text: str) -> None:
        if len(new_text) == 0 or not os.path.exists(new_text):
            self.ui.pushButton_process.setEnabled(False)
        else:
            self.ui.pushButton_process.setEnabled(True)

    @pyqtSlot()
    def update_checkbox_launcher(self):
        self.m_worker.choice_patch_launcher = self.ui.checkBox_Launcher.isChecked()

    @pyqtSlot()
    def update_checkbox_999(self):
        self.m_worker.choice_patch_999 = self.ui.checkBox_999.isChecked()

    @pyqtSlot()
    def update_checkbox_vlr(self):
        self.m_worker.choice_patch_vlr = self.ui.checkBox_VLR.isChecked()

    @pyqtSlot(str)
    def change_progress_text(self, text):
        self.ui.textEdit_log.append(text)

    @pyqtSlot()
    def run_process(self) -> None:
        self.update_ui(False)
        self.ui.textEdit_log.clear()
        self.m_worker.signal_apply_patch.emit(self.ui.lineEdit_gamePath.text())

    @pyqtSlot(str)
    def handle_apply_patch_result(self, error: str) -> None:
        self.ui.textEdit_log.append(error)
        self.update_ui(True)

    def update_ui(self, state: bool) -> None:
        self.ui.lineEdit_gamePath.setEnabled(state)
        self.ui.pushButton_browse.setEnabled(state)
        self.ui.pushButton_process.setEnabled(state)
