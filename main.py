import sys
import time
import typing
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QDesktopWidget,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QGridLayout,
    QDialog,
)
from PyQt5.QtCore import QObject, pyqtSignal, QThreadPool, Qt
from webdriver_manager.chrome import ChromeDriverManager
from exploits import (
    WeakPasswordExploit,
    SQLInjectionExploit,
    XSSAttackExploit,
    SensitivePathsExploit,
)
from utils import url_validator, WriteExcel
from countermeasures import get_countermeasure

found_vulnerabilities: int = 0


class FindIfTasksAlive(QObject):
    response = pyqtSignal(str)
    tasks_finished = pyqtSignal()

    def __init__(
        self,
        tasks: typing.List[QThreadPool],
        run_exploit_search_button,
    ):
        super().__init__()
        self.tasks = tasks
        self.run_exploit_search_button = run_exploit_search_button

    def run(self):
        while self.tasks:
            time.sleep(0.5)

        self.response.emit(
            f"Seeking for exploits is finished. Found {found_vulnerabilities}/4 vulnerabilities."
        )
        self.run_exploit_search_button.setEnabled(True)
        self.tasks_finished.emit()


class ExploitTask(QObject):
    response = pyqtSignal(str, str, str)

    def __init__(
        self,
        exploit: typing.Type[object],
        url: str,
    ):
        super().__init__()
        self.is_killed = False
        self.exploit = exploit
        self.url = url

    def run(self):
        exploit_instance = self.exploit(self.url)
        try:
            response_text, response_status = exploit_instance.run()
            if not self.is_killed:
                self.response.emit(
                    response_text, response_status, exploit_instance.__class__.__name__
                )
        except Exception as e:
            self.response.emit(
                f"Error occurred while using exploit {exploit_instance.__class__.__name__}. Skipping..",
                "red",
                exploit_instance.__class__.__name__,
            )

    def kill(self):
        self.is_killed = True


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.thread_pool = QThreadPool()
        self.tasks = []
        self.responses = []

    def initUI(self):
        self.resize(1000, 600)
        self.center()
        self.setWindowTitle("Website's exploits seeker")
        self.setFixedSize(self.size())

        self.logs_textbox = QTextEdit(self)
        self.logs_textbox.setReadOnly(True)
        self.logs_textbox.setMinimumSize(900, 400)

        self.url_input_label = QLabel("Enter URL for exploits search:")
        self.url_input = QLineEdit()

        self.run_exploit_search_button = QPushButton("Start seeking for exploits", self)
        self.run_exploit_search_button.clicked.connect(self.run_on_click)

        # Add clear button
        self.clear_logs_button = QPushButton("Clear", self)
        self.clear_logs_button.clicked.connect(self.clear_logs)

        # Add how it works button
        self.how_it_works_button = QPushButton("How it works", self)
        self.how_it_works_button.clicked.connect(self.display_how_it_works)
        
        # Show Countermeasures button
        self.show_countermeasures_button = QPushButton('Show Countermeasures', self)
        self.show_countermeasures_button.clicked.connect(self.show_countermeasures)
      

        url_layout = QHBoxLayout()
        url_layout.addWidget(self.url_input_label)
        url_layout.addWidget(self.url_input)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.run_exploit_search_button)
        button_layout.addWidget(self.clear_logs_button)
        button_layout.addWidget(self.how_it_works_button)
        button_layout.addWidget(self.show_countermeasures_button)

        layout = QVBoxLayout()
        layout.addLayout(url_layout)
        layout.addLayout(button_layout)
        layout.addWidget(self.logs_textbox)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.show()
        
    def show_countermeasures(self):
        countermeasures_text = get_countermeasure()
        QMessageBox.information(self, "Countermeasures", countermeasures_text)


    def clear_logs(self):
        self.logs_textbox.clear()

    def display_how_it_works(self):
        message_box = QMessageBox()
        message_box.setWindowTitle("How it works")
        message_box.setText("This tool seeks for vulnerabilities in websites by testing different common exploits such as SQL Injection, XSS, etc. It injects various payloads to test if the website is vulnerable and logs the results here.")
        message_box.exec_()

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        window = self.geometry()
        self.move(
            (screen.width() - window.width()) // 2,
            (screen.height() - window.height()) // 2,
        )

    def run_on_click(self):
        if len(self.url_input.text()) > 3 and url_validator(self.url_input.text()):
            self.log(
                message=f"Successfully validated URL : {url_validator(self.url_input.text())}",
                color="black",
            )

            global found_vulnerabilities
            found_vulnerabilities = 0

            self.run_exploit_search_button.setEnabled(False)

            exploit_classes = [
                WeakPasswordExploit,
                SQLInjectionExploit,
                XSSAttackExploit,
                SensitivePathsExploit,
            ]

            for exploit_class in exploit_classes:
                exploit = ExploitTask(exploit=exploit_class, url=self.url_input.text())
                self.tasks.append(exploit)
                exploit.response.connect(self.add_to_responses)
                exploit.response.connect(self.log)
                exploit.response.connect(self.remove_task)
                self.thread_pool.start(exploit.run)

            find_alive_tasks = FindIfTasksAlive(
                self.tasks, self.run_exploit_search_button
            )
            find_alive_tasks.tasks_finished.connect(self.show_save_report_dialog)
            find_alive_tasks.response.connect(self.log)
            self.thread_pool.start(find_alive_tasks.run)
        else:
            error_message_box = QMessageBox()
            error_message_box.setWindowTitle("Error")
            error_message_box.setText("Enter a valid URL.")
            error_message_box.setIcon(QMessageBox.Warning)
            error_message_box.exec_()

    def remove_task(self):
        self.tasks.pop(0)

    def add_to_responses(self, text, status, exploit_name):
        self.responses.append([exploit_name, text, status == "green"])

    def log(self, message: str, color: str = "black", *args) -> None:
        global found_vulnerabilities

        if color == "green":
            self.logs_textbox.setTextColor(Qt.green)
            found_vulnerabilities += 1
        elif color == "white":
            self.logs_textbox.setTextColor(Qt.white)
        else:
            self.logs_textbox.setTextColor(Qt.black)

        self.logs_textbox.append(f"[| EXPLOIT SEARCH |] : {message}")

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Message",
            "Do you really want to quit?",
            QMessageBox.Yes,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def show_save_report_dialog(self):
        save_dialog = QDialog(self)
        save_dialog.setWindowTitle("Report")

        message_label = QLabel("Do you want to save report?")

        save_button = QPushButton("Save")
        save_button.clicked.connect(lambda: self.save(save_dialog))
        dont_save_button = QPushButton("Don't save")
        dont_save_button.clicked.connect(save_dialog.reject)

        dialog_layout = QGridLayout()
        dialog_layout.addWidget(message_label, 0, 0, 1, 2)
        dialog_layout.addWidget(save_button, 1, 0)
        dialog_layout.addWidget(dont_save_button, 1, 1)
        save_dialog.setLayout(dialog_layout)

        save_dialog.exec_()

    def save(self, dialog):
        writer = WriteExcel("total.xlsx")
        writer.write(data=self.responses)
        dialog.accept()

def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.log("Successfully initialized application.")
    sys.exit(app.exec_())


if __name__ == "__main__":
    ChromeDriverManager().install()
    main()
