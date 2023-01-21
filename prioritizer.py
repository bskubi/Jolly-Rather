import random

class Task:
	default_marks = None

	def __init__(self, desc = "", marks = None):
		self.desc = desc
		if marks is None:
			self.marks = Task.S2M(Task.default_marks)
		else:
			self.marks = marks

	def MarksMatch(self, marks, ignore_none = True):
		for mark in marks.keys():
			if mark not in self.marks.keys() or (marks[mark] is not None and self.marks[mark] != marks[mark]):
				return False
		return True

	def SetMarks(self, marks, ignore_none = True):
		for k, v in marks.items():
			if v is not None:
				self.marks[k] = v

	#Converts a tokenizeable string to list of marks
	#If a token starts with !, the mark is set to false, otherwise it's set to true
	@classmethod
	def S2M(cls, s = ""):
		if s == "":
			s = Task.default_marks
		marks = {}
		s = s.split()
		for t in s:
			if t[0] == "!":
				marks[t[1:]] = False
			else:
				marks[t] = True
		return marks

	def __eq__(self, desc):
		return self.desc == desc

	def __str__(self):
		return self.desc

#Uses the followin marks:
# m = marked 
# d = done
# n = next comparison (untried)
# r = rejected vs. most recent marked option

class Prioritizer:
	def __init__(self, tasks = [], callbacks = {}):
		self.tasks = tasks
		self.callbacks = callbacks
		self.callbacks.setdefault("do_task", Prioritizer.Pass)
		self.callbacks.setdefault("compare_tasks", Prioritizer.Pass)

	@classmethod
	def SetMarkDefaults(cls):
		Task.default_marks = "!m !d !n !r"

	@classmethod
	def Pass(cls, args):
		return None

	def Prioritize(self):
		while not self.Finished():
			self.PrioritizeStep()

	def PrioritizeStep(self):
		#If there are no (m) tasks but there are (!m !d) tasks, set an (m) task
		self.TrySetFirstTentativeOption1()
		#If there are no (n) tasks, either at the beginning of prioritization or after reaching the end of the list, set one if possible
		self.TrySetFirstTentativeOption2()
		#If there are any (n) tasks, advance them to the next one, set the old (n) task to (!n r) and do the "compare_tasks" callback
		self.TryNextOption()
		#If there are any (m !d) tasks with no (!m !r) tasks after them, execute those and only those (m !d) tasks, set them to (d), and convert all (n) to (!n) and (r) to (!r). 
		self.TryExecuteTodos()

	def TrySetFirstTentativeOption1(self):
		opt1 = self.CurrentOption1Index()
		if opt1 is None and not self.Finished():
			opt1 = self.MarkFirstUnmarkedTask()

	#If there is an option 1 task but no option 2 task, set an option 2 task if possible
	def TrySetFirstTentativeOption2(self):
		opt1 = self.CurrentOption1Index()
		opt2 = self.CurrentOption2Index()
		if opt1 is not None and opt2 is None:
			first_untried = self.Index(Task.S2M("!m !n !r"), start_index = opt1)
			if first_untried is not None:
				self.tasks[first_untried].SetMarks(Task.S2M("n"))
				return first_untried

	#First, asks user to select between last mark and current next option
	#Marks the current next option if the user wants
	#Then attempts to advance from the current to the next (n) option.
	def TryNextOption(self):
		old_next = self.CurrentOption2Index()
		if old_next is not None:
			opt1 = self.tasks[self.CurrentOption1Index()]
			opt2 = self.tasks[self.CurrentOption2Index()]
			choice = self.callbacks["compare_tasks"](opt1, opt2, self)
			if choice == "1":
				self.RejectCurrentOption2()
			elif choice == "2":
				opt2i = self.CurrentOption2Index()
				self.tasks[opt2i].SetMarks(Task.S2M("m !n"))
				new_next = self.NextOption2Index()
				if new_next is not None:
					self.tasks[new_next].SetMarks(Task.S2M("n"))

	def TryExecuteTodos(self):
		if self.ReadyTodo():
			todos = self.GetSequentialTodos()
			for todo in todos:
				self.callbacks["do_task"](self.tasks[todo], self)
				self.tasks[todo].SetMarks(Task.S2M("d"))
			unmarked = self.AllIndices(Task.S2M("!m"))
			for un in unmarked:
				self.tasks[un].SetMarks(Task.S2M("!n !r"))

	def AllIndices(self, marks, start_index = 0, reverse = False, bounded = False):
		indices = self.GetIndices(start_index, reverse, bounded)
		matching_indices = []
		for i in indices:
			if self.tasks[i].MarksMatch(marks):
				matching_indices.append(i)
		return matching_indices

	def Find(self, marks, start_index = 0, reverse = False, bounded = False, skip = 0):
		i = self.Index(marks, start_index, reverse, bounded, skip)
		return self.tasks[i] if i is not None else None

	def GetIndices(self, start_index, reverse, bounded):
		if start_index is None:
			return None
		indices = list(range(len(self.tasks)))
		if not reverse and not bounded:
			indices = indices[start_index:] + indices[:start_index]
		elif not reverse and bounded:
			indices = indices[start_index:]
		elif reverse and not bounded:
			indices =  indices[start_index + 1:][::-1] + indices[0:start_index+1][::-1]
		elif reverse and bounded:
			indices = indices[0:start_index+1][::-1]
		return indices

	def Index(self, marks, start_index = 0, reverse = False, bounded = False, skip = 0):
		indices = self.GetIndices(start_index, reverse, bounded)
		for i in indices:
			if self.tasks[i].MarksMatch(marks):
				if skip == 0:
					return i
				else:
					skip -= 1

		return None

	def Finished(self):
		finished = len(self.AllIndices(Task.S2M("!d"))) == 0
		return finished

	def IdentifiedTodo(self):
		current_mark = self.Index(Task.S2M("m !d"), reverse = True)
		if current_mark is not None:
			next_untried_option = self.Index("!m !n !r", start_index = current_mark + 1)
			if next_untried_option is not None:
				return False
			return True
		return False

	def UnmarkedTasksRemain(self):
		return self.Index(Task.S2M("!m")) is not None

	def NoMarkedTasks(self):
		return self.Index(Task.S2M("m")) is None

	def AllTasksMarked(self):
		return self.Index(Task.S2M("!m")) is None

	def MarkFirstUnmarkedTask(self):
		first_unmarked = self.Index(Task.S2M("!m"))
		if first_unmarked is not None:
			self.tasks[first_unmarked].SetMarks(Task.S2M("m"))

	def SetCallback(self, callback_type, callback):
		self.callbacks[callback_type] = callback

	#If no tasks are marked and there are unmarked tasks, places a starting mark on the first unfinished task.
	def HandleStartingMark(self):
		if self.UnmarkedTasksRemain() and self.NoMarkedTasks():
			self.MarkFirstUnmarkedTask()

	def CurrentOption1Index(self):
		return self.Index(Task.S2M("m !d"), reverse = True)

	def CurrentOption2Index(self):
		return self.Index(Task.S2M("n"))

	def NextOption2Index(self):
		opt1 = self.CurrentOption1Index()
		if opt1 is not None:
			opt2 = self.Index(Task.S2M("!m !d !n !r"), start_index = opt1)
			return opt2

	def RejectCurrentOption2(self):
		opt2 = self.CurrentOption2Index()
		if opt2 is not None:
			self.tasks[opt2].SetMarks(Task.S2M("!n r"))

	def ReadyTodo(self):
		opt1 = self.CurrentOption1Index()
		if opt1 is not None:
			all_subsequent_unmarked = set(self.AllIndices(Task.S2M("!m")))
			all_subsequent_rejected = set(self.AllIndices(Task.S2M("r")))
			if all_subsequent_unmarked == all_subsequent_rejected:
				return True
		return False

	def GetSequentialTodos(self):
		if self.ReadyTodo():
			todos = [self.CurrentOption1Index()]
			while todos[-1] > 0:
				prev_priority = self.Index(Task.S2M("m !d"), start_index = todos[-1] - 1, reverse = True, bounded = True)
				prev_unmarked = self.Index(Task.S2M("!m"), start_index = todos[-1], reverse = True, bounded = True)
				if prev_priority is not None and (prev_unmarked is None or prev_priority > prev_unmarked):
					todos.append(prev_priority)
				else:
					break
			return todos

def TestDoTask(action, prioritizer):
	if __name__ == "__main__":
		print("Do", action)
		#input()

def TestCompareTasks(option_1, option_2, prioritizer):

	choice = ""
	while choice not in ["1", "2"]:
		if __name__ == "__main__":
			print("Would you rather:\n1.", option_1, "\n2.", option_2)
		#choice = input("> ")
		choice = ["1", "2"][random.randint(0, 1)]
		if __name__ == "__main__":
			print("Choice:", choice)
	return choice

if __name__ == "__main__":
	Prioritizer.SetMarkDefaults()

	tasks = [Task("A", Task.S2M("m !d !n !r")),
			Task("B",  Task.S2M("!m !d !n !r")),
			Task("C", Task.S2M("!m !d !n !r")),
			Task("D", Task.S2M("m !d !n !r")),
			Task("E", Task.S2M("!m !d !n r")),
			Task("E", Task.S2M("!m !d n !r")),
			Task("F", {"m":True, "d":True, "n":False})]
	p = Prioritizer(tasks)

	
	assert p.Find(Task.S2M("m !d"))  == "A"
	assert p.Find(Task.S2M("m !d"), skip = 1)  == "D"
	assert p.Find(Task.S2M("m !d"), start_index = 1)  == "D"
	assert p.Find(Task.S2M("m !d"), start_index = 1, skip = 1)  == "A"
	assert p.Find(Task.S2M("m !d"), start_index = 5, reverse = True) == "D"
	assert p.Find(Task.S2M("m !d"), start_index = 4, bounded = True) is None
	assert p.Find(Task.S2M("m d"), reverse = True, bounded = True)  is None
	assert p.Find(Task.S2M("!m !d n")) == "E"

	for i in range(100):
		print(">>>>>>>>>>>>>>>>>>>>Test", i)
		tasks2 = [Task("A"),
				Task("B"),
				Task("C"),
				Task("D"),
				Task("E")]

		p2 = Prioritizer(tasks2)
		p2.SetCallback("do_task", TestDoTask)
		p2.SetCallback("compare_tasks", TestCompareTasks)
		p2.Prioritize()