import pickle
import random
from os.path import exists

def orderIndices(list_len, start_index, reverse, bounded):
    indices = range(list_len)
    ordered = []
    n = start_index
    for i in range(list_len):
        ordered.append(n)
        n += 1 if not reverse else -1
        if n == -1:
            if bounded:
                return ordered
            else:
                n = list_len-1
        elif n == list_len:
            if bounded:
                return ordered
            else:
                n = 0
    return ordered

class Event:
    def __init__(self, description = "", marked = False, done = False):
        self.desc = description
        self.marked = marked
        self.done = done

    def Unmarked(self):
        new_event = self
        if new_event.done == False:
            new_event.marked = False
        return new_event

    def __str__(self):
        return self.desc + " marked: " + str(self.marked) + " done: " + str(self.done)

    def __eq__(self, a):
        return self.desc == a if type(a) == str else self == a
        

class TodoList:
    def __init__(self):
        self.list = []
        self.nxt = -1
        self.simulate_input = False

    def Complete(self):
        return sum(list(map(lambda x : x.done, self.list))) == len(self.list)

    def NearlyCompletePrompt(self):
        if self.Complete():
            print("You're all finished!")
            return True
        if sum(list(map(lambda x : x.done, self.list))) == len(self.list) - 1:
            print("Your last task: ", self.Find(0, True, False, bounded = True))
            return True
        return False
    
    def Choice(self, choice):

        prev = self.nxt
        self.nxt = self.Index(1, False, False, start_index = self.nxt, bounded = True)
        if choice == "2":
            self.list[prev].marked = True
            
        if self.nxt is None:
            self.DoPrompt()
            return True
        return False

    def StrongChoice(self, choice):
        if choice == "1":
            self.DoPrompt()
        if choice == "2":
            if not self.Choice("2"):
                self.DoPrompt()

    def DoPrompt(self):
        done = False
        while not done:
            print("Your next task is:", self.Find(0, True, False, reverse = True, start_index = -1))
            if not self.simulate_input:
                input("Enter when done>")
            done = self.DoNextTasks()

    def DoNextTasks(self):
        self.list[self.Index(0, True, False, reverse = True, start_index = -1)].done = True
        new_prev = self.Index(0, True, False, reverse = True, start_index = -1, bounded = True)
        if new_prev is None and not self.Complete():
            new_prev = self.Index(0, False, False)
            self.list[new_prev].marked = True
        if self.Complete():
            return True
        self.nxt = self.Index(0, False, False, reverse = False, start_index = new_prev, bounded = True)
        return self.nxt is not None

    def Setup(self):
        while self.AddTaskPrompt():
            continue
        self.Reprioritize()

    def AddTaskPrompt(self):
        desc = input("Task description ['done' to stop]: ")
        if desc in self.list:
            print("Duplicate entry, try again.")
        elif desc == "done":
            return False
        else:
            self.list.append(Event(desc))
        return True
    
    def SavePrompt(self):
        fn = input("Woyora list name:")
        self.Save(fn + ".pickle")

    @classmethod
    def LoadPrompt(self):
        fn = input("Woyora list name:")
        return TodoList.Load(fn + ".pickle")

    def Save(self, fn):
        pickle.dump(self, open(fn, "wb"))

    @classmethod
    def Load(self, fn):
        if exists(fn):
            return pickle.load(open(fn, "rb"))
        return None
    
    def Reprioritize(self):
        for i in range(len(self.list)):
            self.list[i].marked = self.list[i].done
        
        self.MarkFirstUndone()
        self.nxt = self.Index(0, False, False)
        
    def MarkFirstUndone(self):
        self.list[self.Index(0, False, False)].marked = True

    def Find(self, n, marked = None, done = None, reverse = False, start_index = 0, bounded = False):
        i = self.Index(n, marked, done, reverse, start_index, bounded)
        return self.list[i] if i is not None else None

    def Index(self, n, marked = None, done = None, reverse = False, start_index = 0, bounded = False):
        if start_index < 0:
            start_index = start_index + len(self.list)
        indices = orderIndices(len(self.list), start_index, reverse, bounded)
        ret = None
        for i in indices:
            match = self.CheckMatch(self.list[i], marked, done)
            if match and n == 0:
                return i
            n -= match
        return None

    def CheckMatch(self, task, marked, done):
        return True if (marked is None or task.marked == marked) and (done is None or task.done == done) else False

    def Undo(self):
        pass

    def Redo(self):
        pass

    def PromptChoice(self, a, b):
        options = {"1":[a.desc, self.Choice, "1"], "2":[b.desc, self.Choice, "2"], "3":["Strong select " + a.desc, self.StrongChoice, "1"], "4":["Strong select "+b.desc, self.StrongChoice, "2"], "5":["Save", self.SavePrompt],
                   "6":["Reprioritize", self.Reprioritize], "7":["Undo", self.Undo], "8":["Redo", self.Redo], "9":["Main menu", None]}
        display = '\n'.join(list(map(lambda k : k + ". " + options[k][0], options.keys())))

        print(display)
        choice = ""
        while choice not in options.keys():
            choice = input(">") if not self.simulate_input else ["1", "2"][random.randint(0, 1)]
        params = options[choice][2] if len(options[choice]) == 3 else []
        if options[choice][1] is not None:
            options[choice][1](*params)
            return True
        return False
        
    def WouldYouRather(self):
        if len(self.list) == 0:
            self.Setup()
        while not self.NearlyCompletePrompt():
            a_i = self.Index(0, True, False, start_index = -1, reverse = True)
            b = self.Find(0, False, False, start_index = self.nxt, reverse = False, bounded = True)
            a = self.list[a_i]
            if not self.PromptChoice(a, b):
                break
        

    def TestFindFunctions(self):
        self.list = [Event("A", True, False),
                     Event("B", False, False),
                     Event("C", False, False),
                     Event("D", True, False),
                     Event("E", False, False),
                     Event("F", False, False),
                     Event("G", True, True)]
        self.nxt = 4

        assert self.Find(0, True, False) == "A", self.FindInOrder(0, True, False)
        assert self.Find(0, True, True) == "G", self.FindInOrder(0, True, True)
        assert self.Find(0, False) == "B", self.FindInOrder(0, False)
        assert self.Find(0, True) == "A", self.FindInOrder(0, True)
        assert self.Find(1, False, False) == "C", self.FindInOrder(1, False, False)
        assert self.Find(0, False, False, True) == "F", self.FindInOrder(0, False, False, True)
        assert self.Find(1, False, False, True) == "E", self.FindInOrder(1, False, False, True)
        assert self.Find(0, True, False, start_index = 3) == "D", self.FindInOrder(0, True, False, start_index = 3)
        assert self.Find(1, True, False, start_index = 3) == "A", self.FindInOrder(1, True, False, start_index = 3)
        assert self.Find(0, False, False, start_index = 3, reverse = True) == "C", self.FindInOrder(0, False, False, start_index = 3, reverse = True)
        assert self.Find(1, False, False, start_index = 3, reverse = True) == "B", self.FindInOrder(1, False, False, start_index = 3, reverse = True)

todo = TodoList()
todo.TestFindFunctions()
while True:
    todo = TodoList()
    ld = TodoList.LoadPrompt()
    todo = ld if ld is not None else todo
    todo.WouldYouRather()
