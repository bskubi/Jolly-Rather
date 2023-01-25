import sys
import os
from prioritizer_fvp_interface import *
from PyQt5.QtWidgets import QApplication, QMainWindow
from jolly_rather_ui import *
from PyQt5 import QtCore, QtGui, QtWidgets

app = QApplication(sys.argv)

class PrioritizerUI(QMainWindow, Ui_JollyRatherMainWindow):
    def __init__(self):
        super().__init__()

        self.setupUi(self)
        self.setup_connections()
        self.setup_prioritizer()
        self.show()

    def setup_connections(self):
        self.opt1.clicked.connect(self.click_opt1)
        self.opt2.clicked.connect(self.click_opt2)
        self.todo_list.textChanged.connect(self.edit_todo_list)

    def setup_prioritizer(self):
        self.prioritizer = PrioritizerFVPInterface()
        self.prioritizer.callbacks["option"] = self.handle_choose
        self.prioritizer.callbacks["execute"] = self.handle_execute
        self.prioritizer.callbacks["finished"] = self.handle_finished
        self.prioritizer.callbacks["update"] = self.handle_prioritizer_update

        if os.path.exists("jollyrather_save.txt"):
            with open("jollyrather_save.txt") as f:
                self.todo_list.setPlainText(f.read())

        self.edit_todo_list()

    def load_todo_list_to_prioritizer(self):
        lines = self.todo_list.toPlainText().split('\n')
        content_lines = [line for line in lines if line.strip() != ""]
        self.prioritizer.tasks = []
        for line in content_lines:
            self.prioritizer.tasks.append(Task(desc = line))

    def edit_todo_list(self):
        self.load_todo_list_to_prioritizer()
        self.prioritizer.respond_to_command("setup")

    def click_opt1(self):
        self.prioritizer.respond_to_command("opt1")
    def click_opt2(self):
        self.prioritizer.respond_to_command("opt2")
        
    def click_strikeoff(self):
        self.prioritizer.respond_to_command("exec")
        
    def handle_choose(self, opt1, opt2):
        self.headline_label.setText("Would you rather...")
        self.opt1.setText(opt1.desc)
        self.opt2.setText(opt2.desc)
        self.opt2.setVisible(True)
        self.opt1.clicked.disconnect()
        self.opt2.clicked.disconnect()
        self.opt1.clicked.connect(self.click_opt1)
        self.opt2.clicked.connect(self.click_opt2)

    def handle_execute(self, task):
        self.headline_label.setText("It's time to...")
        self.opt1.setText(task.desc)
        self.opt2.setVisible(False)
        self.opt1.disconnect()
        self.opt1.clicked.connect(self.click_strikeoff)

    def handle_finished(self):
        self.headline_label.setText("Your todo list is to-done!")
        self.opt1.setVisible(False)
        self.opt2.setVisible(False)

    def handle_prioritizer_update(self):
        self.todo_list.textChanged.disconnect()
        cursor = self.todo_list.textCursor()
        pos = cursor.position()
        todo_text = self.todo_list.toPlainText()
        before_cursor = todo_text[0:pos]
        after_cursor = todo_text[pos:]
        cursor_line = len(before_cursor.split('\n'))-1

        lines = []
        for i in range(len(self.prioritizer.tasks)):
            task = self.prioritizer.tasks[i]
            if task["$"]:
                lines.append("$ " + task.desc)
            elif task["#"]:
                lines.append("# " + task.desc)
            elif task["*"]:
                lines.append("* " + task.desc)
            elif task["?"]:
                lines.append("? " + task.desc)
            else:
                lines.append("  " + task.desc)
        lines.append("")
        self.todo_list.setPlainText('\n'.join(lines))

        if cursor_line == len(lines)-2 and pos < len(self.todo_list.toPlainText())-1:
            cursor.setPosition(pos+1)
        else:
            cursor.setPosition(pos)

        self.todo_list.setTextCursor(cursor)
        self.todo_list.textChanged.connect(self.edit_todo_list)

    def closeEvent(self, event):
        with open("jollyrather_save.txt", "w") as f:
            f.write(self.todo_list.toPlainText())


ui = PrioritizerUI()
sys.exit(app.exec_())