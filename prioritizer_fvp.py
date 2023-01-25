from prioritizer import *

class PrioritizerFVP(Prioritizer):
    def __init__(self):
        super().__init__()

    def setup_marks(self):
        for i in range(len(self.tasks)):
            task = self.tasks[i]
            if task.desc[0] == "*":
                self.tasks[i].desc = PrioritizerFVP.trim_beginning_whitespace(task.desc[1:])
                self.tasks[i].update("* !$ !# !?")
            elif task.desc[0] == "?":
                self.tasks[i].desc = PrioritizerFVP.trim_beginning_whitespace(task.desc[1:])
                self.tasks[i].update("!* !$ !# ?")
            elif task.desc[0] == "#":
                self.tasks[i].desc = PrioritizerFVP.trim_beginning_whitespace(task.desc[1:])
                self.tasks[i].update("# * !$ !?")
            elif task.desc[0] == "$":
                self.tasks[i].desc = PrioritizerFVP.trim_beginning_whitespace(task.desc[1:])
                self.tasks[i].update("$ * !# !?")
            else:
                self.tasks[i].desc = PrioritizerFVP.trim_beginning_whitespace(task.desc)
                self.tasks[i].update("!$ !* !# !?")
        if len(self.tasks) == 1 and not self.tasks[0]["$"]:
            self.tasks[0].update(Task.s2m("#"))
        if len(self.tasks) >= 1:
            self.tasks[0].update(Task.s2m("*"))
        if len(self.tasks) >= 2:
            self.tasks[1].update(Task.s2m("?"))
        self.fix_marks()
        self.callbacks["update"]()

    @classmethod
    def trim_beginning_whitespace(cls, s):
        replace = ""
        print(s)
        for i in range(len(s)):
            if s[i] not in [" ", "\t"]:
                replace = s[i:]
                break
        print("'"+replace+"'")
        return replace

    def fix_marks(self):
        self.fix_strikeoff_marks()
        self.fix_exec_marks()
        self.fix_star_marks()
        self.fix_opt2_marks()

    def fix_strikeoff_marks(self):
        for i in self.all_indices(Task.s2m("$")):
            self.tasks[i].update(Task.s2m("* !# !?"))

    def fix_exec_marks(self):
        exec_marks = self.all_indices(Task.s2m("#"))
        for i in exec_marks[0:len(exec_marks)-1]:
            self.tasks[i].update(Task.s2m("!#"))
        if len(exec_marks) > 0:
            self.tasks[exec_marks[-1]].update(Task.s2m("* !$ !?"))

    def fix_star_marks(self):
        star_marks = self.all_indices(Task.s2m("*"))
        for i in star_marks:
            self.tasks[i].update(Task.s2m("!?"))
        if self.ready_to_exec():
            self.tasks[self.index(Task.s2m("*"), start_index = -1, reverse = True)].update(Task.s2m("#"))

    def fix_opt2_marks(self):
        opt2_marks = self.all_indices(Task.s2m("?"))
        for i in opt2_marks[0:len(opt2_marks)-1]:
            self.tasks[i].update(Task.s2m("!?"))
        if len(opt2_marks) > 0 and ((self.opt(1) is not None and (self.opt(1) > opt2_marks[-1])) or self.exec() is not None):
            self.tasks[opt2_marks[-1]].update("!?")
        if self.opt(2) is None and self.exec() is None:
            self.add_opt2()

    #If in an option state:
    #Clears previous ? and adds ? to next !* mark if possible
    #If no subsequent !* tasks exist, adds # to last *
    def advance_option(self, star_opt2):
        if self.option_state():
            next_opt2 = self.next_opt2()
            old_mark = "!?" if not star_opt2 else "!? *"
            self.tasks[self.opt(2)].update(old_mark)
            if next_opt2 is not None:
                self.tasks[next_opt2].update("?")
            else:
                self.tasks[self.opt(1)].update("#")

    #Change the last (?) task to (!? *)
    def star_opt2(self):
        if self.option_state():
            self.tasks[self.opt(2)].update(Task.s2m("!? *"))

    #Change the last (#) task to (!# $).
    #If there was no prior (* !$) task but there are (!*) tasks, set the first (!*) task to (*) and if possible set the next (!*) task to (?)
    #If there are no (!*) tasks or there were no (!*) tasks between it and the prior (* !$) task,
    #Mark the most immediate prior (* !$) task as ($)
    #If there was a prior (!*) task
    def strikeoff_task(self):
        if self.exec_state():
            self.strikeoff_last_exec()
            if not self.finished_state():
                print("unfinished")
                if self.index(Task.s2m("* !$")) is None:
                    print("no *")
                    self.add_opt1()
                    self.add_opt2()
                if self.on_last_task() or self.sequential_exec():
                    print("on last task")
                    self.exec_last_unfinished_task()
                elif self.opt(2) is None:
                    print("no opt 2")
                    self.add_opt2()

    def option_state(self):
        return self.opt(1) is not None and self.opt(2) is not None

    def exec_state(self):
        return self.exec() is not None

    def finished_state(self):
        return self.index(Task.s2m("!$")) is None

    def opt(self, i):
        if i == 1:
            return self.index(Task.s2m("* !# !$"), start_index = -1, reverse = True)
        elif i == 2:
            return self.index(Task.s2m("?"), start_index = -1, reverse = True)

    def add_opt1(self):
        if self.next_opt1() is not None:
            self.tasks[self.next_opt1()].update(Task.s2m("*"))

    def add_opt2(self):
        next_opt2 = self.next_opt2(self.opt(1))
        print(self.opt(1), next_opt2)
        if next_opt2 is not None:
            self.tasks[next_opt2].update(Task.s2m("?"))

    def next_opt1(self):
        next_opt1 = self.index(Task.s2m("* !$"))
        if next_opt1 is None:
            return self.index(Task.s2m("!*"))
        return next_opt1

    def next_opt2(self, start = None):
        start = self.opt(2) if start is None else start
        return self.index(Task.s2m("!* !?"), start_index = start, bounded = True)

    def exec(self):
        return self.index(Task.s2m("#"), start_index = -1, reverse = True)

    def ready_to_exec(self):
        last_star = self.index(Task.s2m("*"), start_index = -1, reverse = True)
        last_opt = self.index(Task.s2m("!*"), start_index = -1, reverse = True)
        return last_star > last_opt

    def exec_last_unfinished_task(self):
        self.tasks[self.index(Task.s2m("!$"), start_index = -1, reverse = True)].update("* # !?")

    def strikeoff_last_exec(self):
        last_exec = self.exec()
        self.tasks[last_exec].update(Task.s2m("!# $"))
        return last_exec

    def sequential_exec(self):
        last_strikeoff = self.index(Task.s2m("$"), start_index = -1, reverse = True)
        if last_strikeoff is not None and self.index(Task.s2m("!$"), start_index = last_strikeoff, bounded = True) is None:
            prior_unfinished_starred = self.index(Task.s2m("* !$"), start_index = last_strikeoff, reverse = True, bounded = True)
            prior_unfinished_unstarred = self.index(Task.s2m("!*"), start_index = last_strikeoff, reverse = True, bounded = True)
            return prior_unfinished_starred is None or prior_unfinished_unstarred is None or prior_unfinished_starred > prior_unfinished_unstarred
        return False

    def on_last_task(self):
        return len(self.all_indices(Task.s2m("!$"))) == 1