class Task(dict):
	default_marks = None

	def __init__(self, desc = "", marks = None, extend_with_defaults = True):
		self.desc = desc
		if marks is not None:
			self.update(marks)
		elif Task.default_marks is not None:
			for k, v in Task.default_marks.items():
				self.setdefault(k, v)

	def update(self, d):
		if type(d) == str:
			d = Task.s2m(d)
		super().update(dict(d))

	def marked_as(self, marks):
		for k, v in marks.items():
			if k in self.keys() and self[k] != v:
				return False
		return True

	@classmethod
	def s2m(cls, s):
		marks = {}
		if s is None:
			return {}
		for t in s.split():
			if len(t) > 1 and t[0] == "!":
				marks[t[1:]] = False
			else:
				marks[t] = True
		return marks

	def __str__(self):
		return self.desc

class Prioritizer:
	def __init__(self):
		self.tasks = []
		self.callbacks = {}

	#Abstract prioritization step, to be instantiated by child classes
	def prioritize_step(self):
		pass

	def default_callback(self, *args):
		pass

	def load_todo_list(self, todo_list):
		pass

	#Returns whether or not all tasks are marked (d)
	def finished(self):
		return len(self.all_indices(Task.s2m("d"))) == len(self.tasks)

	#Returns the index of a task marked as "marks", skipping a number of matches equal to "skip"
	#And going in reverse or being bounded if specified
	def index(self, marks, skip = 0, start_index = 0, reverse = False, bounded = False):
		for i in self.indices(start_index, reverse, bounded):
			if self.tasks[i].marked_as(marks):
				if skip == 0:
					return i
				else:
					skip -= 1
		return None

	#Returns all indices at which a task marked as specified exists
	def all_indices(self, marks, start_index = 0):
		indices = []
		for i in range(start_index, len(self.tasks)):
			if self.tasks[i].marked_as(marks):
				indices.append(i)
		return indices

	#Gets a set of task list-specific indices starting at start_index, going forward or in reverse,
	#And stopping at zero or the end of the list if bounded is true, otherwise wrapping around back to start_index +/- 1
	def indices(self, start_index = 0, reverse = False, bounded = False):
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