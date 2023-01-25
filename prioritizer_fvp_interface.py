from prioritizer_fvp import *

class PrioritizerFVPInterface(PrioritizerFVP):
    def __init__(self):
        super().__init__()
        Task.default_marks = Task.s2m("!* !$ !# !?")

    #Updates prioritization state based on command
    def respond_to_command(self, cmd):
        if cmd == "setup":
            self.setup_marks()
        if cmd == "opt1":
            self.advance_option(False)
        elif cmd == "opt2":
            self.advance_option(True)
        elif cmd == "exec":
            self.strikeoff_task()
        self.report_state()

    #Runs callbacks to report prioritization state
    def report_state(self):
        if self.option_state():
            self.callbacks["option"](self.tasks[self.opt(1)], self.tasks[self.opt(2)])
        elif self.exec_state():
            self.callbacks["execute"](self.tasks[self.exec()])
        elif self.finished_state():
            self.callbacks["finished"]()
        self.callbacks["update"]()