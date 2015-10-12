#----------------------------------------------------------------------#
# ApproxSRPTE.py
#
# This application simulates a single server with Poisson arrivals
# and processing times of a general distribution. There are errors in
# time estimates within a range. Arrivals are assigned to SRPT classes
# using the methods described in Adaptive and Scalable Comparison
# Scheduling.
#
# Rachel Mailach
#----------------------------------------------------------------------#

from Tkinter import *
from datetime import datetime
from math import log
import copy
import random
import tkMessageBox
import ttk
import tkFileDialog
import csv
import operator

NumJobs = []
TimeSys = []
ProcTime = []
PercError = []

#----------------------------------------------------------------------#
# Class: GUI
#
# This class is used as a graphical user interface for the application.
#
#----------------------------------------------------------------------#
class GUI(Tk):
	def __init__(self, master):
		Tk.__init__(self, master)
		self.master = master        # reference to parent
		self.statusText = StringVar()
		random.seed(datetime.now())

		# Create the input frame
		self.frameIn = Input(self)
		self.frameIn.pack(side=TOP, fill=X, expand=False, padx = 5, pady =5, ipadx = 5, ipady = 5)     

		# Create the output frame
		self.frameOut = Output(self)
		self.frameOut.pack(side=TOP, fill=BOTH, expand=True, padx = 5, pady =5, ipadx = 5, ipady = 5)

		# Bind simulate button
		self.bind("<<input_simulate>>", self.submit)

		# Bind save button
		self.bind("<<output_save>>", self.saveData)

		# Bind clear button
		self.bind("<<output_clear>>", self.clearConsole)

		# Status Bar
		status = Label(self.master, textvariable=self.statusText, bd=1, relief=SUNKEN, anchor=W)
		status.pack(side=BOTTOM, anchor=W, fill=X)      

		# Initialize console
		self.makeConsole()
		self.printIntro()
		self.updateStatusBar("Waiting for submit...")

	def makeConsole(self):
		consoleFrame = Frame(self.frameOut)
		consoleFrame.pack(side=TOP, expand=True, fill=BOTH, padx=5, pady=5)

		self.console = Text(consoleFrame, wrap = WORD)
		scrollbar = Scrollbar(consoleFrame)

		self.console.config(state=DISABLED)     # start with console as disabled (non-editable)
		scrollbar.config(command = self.console.yview)
		self.console.config(yscrollcommand=scrollbar.set)

		self.console.grid(column=0, row=0, sticky='NSEW')
		scrollbar.grid(column=1, row=0, sticky='NS')

		#DOES NOTHING??
		self.grid_columnconfigure(0, weight=1) 
		self.grid_rowconfigure(0, weight=1)


	def writeToConsole(self, text = ' '):
		self.console.config(state=NORMAL)       # make console editable
		self.console.insert(END, '%s\n'%text)
		self.update()
		self.console.config(state=DISABLED)     # disable (non-editable) console

	def saveData(self, event):
		# Get filename
		filename = tkFileDialog.asksaveasfilename(title="Save as...", defaultextension='.txt')
		
		if filename:
			file = open(filename, mode='w')
			data = self.console.get(1.0, END)
			encodedData = data.encode('utf-8')
			text = str(encodedData)
		
			file.write(text)

			file.close()

	# Empty arrivals file at the begining of each simulation
	def clearSavedArrivals(self):
		with open("Arrivals.txt", "w") as myFile:
			myFile.write('JOB NAME,    ARRIVAL TIME,    RPT,     ERPT,     CLASS' + '\n')
		myFile.close()

	def clearConsole(self, event):
		self.console.config(state=NORMAL)       # make console editable
		self.console.delete('1.0', END)
		self.console.config(state=DISABLED)     # disable (non-editable) console

	def updateStatusBar(self, text=' '):
		self.statusText.set(text)
	
	def printIntro(self):
		self.writeToConsole("Approximate SRPTE \n\n This application simulates a single server with Poisson arrivals and processing times of a general distribution. There are errors in time estimates within a range. Arrivals are assigned to SRPT classes using the methods described in Adaptive and Scalable Comparison Scheduling.")

	def printParams(self, arrRate, procRate, percError, numClasses, simLength): 
		self.writeToConsole("--------------------------------------------------------------------------------")
		self.writeToConsole("PARAMETERS:")
		self.writeToConsole("Arrival Rate = %.4f"%arrRate)
		self.writeToConsole("Processing Rate = %.4f"%procRate)
		self.writeToConsole("% Error  = " + u"\u00B1" + " %.4f"%percError)
		self.writeToConsole("Number of Classes = %d"%numClasses)
		self.writeToConsole("Simulation Length = %.4f\n\n"%simLength)

	def calcVariance(self, List, avg):
		var = 0
		for i in List:
			var += (avg - i)**2
		return var/len(List)

	def displayAverageData(self):
		try:
			AvgNumJobs = int(float(sum(NumJobs))/len(NumJobs))
		except ZeroDivisionError:
			AvgNumJobs = 0

		try:
			AvgTimeSys = float(sum(TimeSys))/len(TimeSys)
		except ZeroDivisionError:
			AvgTimeSys = 0.0

		try:
			AvgProcTime = float(sum(ProcTime))/len(ProcTime)
		except ZeroDivisionError:
			AvgProcTime = 0.0

		try:
			VarProcTime = self.calcVariance(ProcTime, AvgProcTime)
		except ZeroDivisionError:
			VarProcTime = 0.0

		try:
			AvgPercError = float(sum(PercError))/len(PercError)
		except ZeroDivisionError:
			AvgPercError = 0.0

		self.writeToConsole('\n\nAverage number of jobs in the system: %.6f' %AvgNumJobs)
		self.writeToConsole('Average time in system, from start to completion: %.6f' %AvgTimeSys)
		self.writeToConsole('Average processing time, based on generated service times: %.6f' %AvgProcTime)
		self.writeToConsole('Variance of processing time: %.6f' %VarProcTime)
		self.writeToConsole('Average percent error: %.2f\n' %AvgPercError)
		#self.writeToConsole('Request order: %s' % ArrivalClass.JobOrderIn)
		self.writeToConsole('Service order: %s\n\n' % MachineClass.JobOrderOut)


				
	def submit(self, event):
		self.updateStatusBar("Simulating...")
		self.clearSavedArrivals()
		I = Input(self)     

		self.printParams(I.valuesList[0], I.valuesList[1], I.valuesList[2], I.valuesList[3], I.valuesList[4])

		main.timesClicked = 0
		
		# Start process
		MC = MachineClass(self)
		MC.run(	I.valuesList[0], I.distList[0],\
				I.valuesList[1], I.distList[1],\
				I.valuesList[2],\
				I.valuesList[3],\
				I.valuesList[4])

		self.displayAverageData()
		self.updateStatusBar("Simulation complete.")


#----------------------------------------------------------------------#
# Class: Input
#
# This class is used as a graphical user interface for a larger
# application.
#
#----------------------------------------------------------------------#
class Input(LabelFrame):
	def __init__(self, master):
		LabelFrame.__init__(self, master, text = "Input")
		self.master = master
		self.arrivalRateInput = DoubleVar()
		self.processingRateInput = DoubleVar()
		self.percentErrorInput = DoubleVar()
		self.numberOfClassesInput = IntVar()
		self.simLengthInput = DoubleVar()
		self.errorMessage = StringVar()

		self.arrivalRateInput.set(1.0)          ##################################CHANGE LATER
		self.processingRateInput.set(0.5)       ##################################CHANGE LATER
		self.percentErrorInput.set(20)          ##################################CHANGE LATER
		self.numberOfClassesInput.set(8)		##################################CHANGE LATER
		self.simLengthInput.set(50.0)           ##################################CHANGE LATER

		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(0, weight=1)

		# Labels
		labels = ['Interarrival Rate (' + u'\u03bb' + ')', 'Processing Rate (' + u'\u03bc' + ')', '% Error', 'Number of Classes', 'Simulation Length']
		r=0
		c=0
		for elem in labels:
			Label(self, text=elem).grid(row=r, column=c)
			r=r+1
		
		Label(self, textvariable=self.errorMessage, fg="red", font=14).grid(row=5, columnspan=4) #error message, invalid input
		Label(self, text=u"\u00B1").grid(row=2, column=1) # +/-

		# Entry Boxes
		self.entry_1 = Entry(self, textvariable = self.arrivalRateInput)
		self.entry_2 = Entry(self, textvariable = self.processingRateInput)
		self.entry_3 = Entry(self, textvariable = self.percentErrorInput)
		self.entry_4 = Entry(self, textvariable = self.numberOfClassesInput)
		self.entry_5 = Entry(self, textvariable = self.simLengthInput)
		self.entry_1.grid(row = 0, column = 2)
		self.entry_2.grid(row = 1, column = 2)
		self.entry_3.grid(row = 2, column = 2)
		self.entry_4.grid(row = 3, column = 2)
		self.entry_5.grid(row = 4, column = 2)


		# Distribution Dropdowns
		self.distributions = ('Select Distribution', 'Poisson', 'Exponential', 'Uniform', 'Custom')
		self.comboBox_1 = ttk.Combobox(self, values = self.distributions, state = 'disabled')
		self.comboBox_1.current(1) # set selection
		self.comboBox_1.grid(row = 0, column = 3)
		self.comboBox_2 = ttk.Combobox(self, values = self.distributions, state = 'readonly')
		self.comboBox_2.current(2) # set default selection                  #####################CHANGE LATER
		self.comboBox_2.grid(row = 1, column = 3)

		# Simulate Button
		self.simulateButton = Button(self, text = "SIMULATE", command = self.onButtonClick)
		self.simulateButton.grid(row = 6, columnspan = 4)

	def onButtonClick(self):
		if (self.getNumericValues() == 0) and (self.getDropDownValues() == 0):
				# Send to submit button in main 
				self.simulateButton.event_generate("<<input_simulate>>")


	def getNumericValues(self):
		try:
				arrivalRate = self.arrivalRateInput.get()
				processingRate = self.processingRateInput.get()
				percentError = self.percentErrorInput.get()
				numberOfClasses = self.numberOfClassesInput.get()
				maxSimLength = self.simLengthInput.get()
		except ValueError:
				self.errorMessage.set("One of your inputs is an incorrect type, try again.")
				return 1

		if arrivalRate <= 0.0:
				self.errorMessage.set("Arrival rate must be non-zero value!")
				return 1
		if processingRate <= 0.0:
				self.errorMessage.set("Processing rate must be non-zero value!")
				return 1
		if numberOfClasses < 1.0:
				self.errorMessage.set("There must be at least one class!")
				return 1		
		if maxSimLength <= 0.0:
				self.errorMessage.set("Simulation length must be non-zero value!")
				return 1
		else:
				self.errorMessage.set("")
				Input.valuesList = [arrivalRate, processingRate, percentError, numberOfClasses, maxSimLength]
				return 0

	def getDropDownValues(self):
		comboBox1Value = self.comboBox_1.get()
		comboBox2Value = self.comboBox_2.get()
		if comboBox2Value == 'Select Distribution':
				self.errorMessage.set("You must select a distribution for the processing rate")
				return 1
		else:
				self.errorMessage.set("")
				Input.distList = [comboBox1Value, comboBox2Value]
				return 0

#----------------------------------------------------------------------#
# Class: Output
#
# This class is used as a graphical user interface for a larger
# application.
#
#----------------------------------------------------------------------#
class Output(LabelFrame):
	def __init__(self, master):
		LabelFrame.__init__(self, master, text = "Output")
		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(0, weight=1)

		buttonFrame = Frame(self)
		buttonFrame.pack(side=BOTTOM, padx=5, pady=5)

		# Clear Button
		self.clearButton = Button(buttonFrame, text = "CLEAR DATA", command = self.onClearButtonClick)
		self.clearButton.grid(row = 2, column = 0)
		
		# Save Button
		self.saveButton = Button(buttonFrame, text = "SAVE DATA", command = self.onSaveButtonClick)
		self.saveButton.grid(row=2, column=1)

	def onClearButtonClick(self):
		# Clear console
		self.clearButton.event_generate("<<output_clear>>")

	def onSaveButtonClick(self):
		# Save data
		self.saveButton.event_generate("<<output_save>>")


#----------------------------------------------------------------------#
# Class: CustomDist
#
# This class is used to allow users to enter a custom distribution.
#
#----------------------------------------------------------------------#
class CustomDist(object):
	def __init__(self, master):
		top = self.top = Toplevel(master)
		top.geometry("500x200")                     # set window size
		top.resizable(0,0)

		self.function = StringVar()

		# Label frame
		frame1 = Frame(top)
		frame1.pack(side=TOP, padx=5, pady=5)
		self.l=Label(frame1, text="Please enter the functional inverse of the distribution of your choice. \nExponential distribution is provided as an example. \nNote: x " + u"\u2265" + " 0", font=("Helvetica", 12), justify=LEFT)
		self.l.pack()

		# Button frame
		frame2 = Frame(top)
		frame2.pack(side=TOP, padx=5, pady=5)
		self.mu=Button(frame2, text=u'\u03bc', command=self.insertMu)
		self.mu.pack(side=LEFT)

		self.u=Button(frame2, text="u", command=self.insertU)
		self.u.pack(side=LEFT)

		self.ln=Button(frame2, text="ln", command=self.insertLn)
		self.ln.pack(side=LEFT)

		# Input frame
		frame3 = Frame(top)
		frame3.pack(side=TOP, padx=5, pady=5)
		self.e = Entry(frame3, textvariable = self.function)
		self.e.insert(0, "-(1/" + u'\u03bc' + ")*ln(u)")
		self.e.pack(fill="both", expand=True)

		frame4 = Frame(top)
		frame4.pack(side=TOP, pady=10)
		self.b=Button(frame4,text='Ok',command=self.cleanup)
		self.b.pack()

	def cleanup(self):
		self.stringEquation=self.convertFunction()
		self.top.destroy()

	def insertMu(self):
		self.e.insert(END, u'\u03bc')

	def insertU(self):
		self.e.insert(END, "u")

	def insertLn(self):
		self.e.insert(END, "ln")

	def convertFunction(self):
		self.stringList = list(self.e.get())
		for i in range(len(self.stringList)):
			if self.stringList[i] == u'\u03bc':
				self.stringList[i] = "procRate"
			elif self.stringList[i] == "u":
				self.stringList[i] = "random.uniform(0.0, 1.0)"
			elif self.stringList[i] == "l" and self.stringList[i+1] == "n":
				self.stringList[i] = "log"
				self.stringList[i+1] = ""
		print "".join(self.stringList)
		return "".join(self.stringList)
		
#----------------------------------------------------------------------#
# Class: Node
#
# This class is used to define the linked list nodes.
#
#----------------------------------------------------------------------#
class Node():
	def __init__(self, job, nextNode = None):
		self.job = job
		self.nextNode = nextNode

#----------------------------------------------------------------------#
# Class: LinkedList
#
# This class is used to make the linked list data structure used to
# store jobs.
#
#----------------------------------------------------------------------#
class LinkedList(object):
	Size = 0

	def __init__(self, head = None):
		self.head = head

    # Insert job into queue (sorted by class, then name)
	def insert(self, job):
		current = self.head		# node iterator, starts at head
		previous = None
		if (current == None):	# if queue is empty, set current job as head
			self.head = Node(job, None)
		else:
			while (current != None) and (job.priorityClass >= current.job.priorityClass) and (job.name > current.job.name):
				previous = current 				# prev = node[i]
				current = current.nextNode 		# current = node[i+1]
			
			# Insert new node after previous before current
			if (previous == None):
				self.head = Node(job, current)
			else:
				previous.nextNode = Node(job, current)

		LinkedList.Size += 1

	# Remove first item in queue
	def removeHead(self):
		if (LinkedList.Size > 0):
			self.head = self.head.nextNode		# move head forward one node
			LinkedList.Size -= 1
		else:
			GUI.writeToConsole(self.master, "ERROR: The linked list is already empty!")

	def clear(self):
		LinkedList.Size = 0
		self.head = None

	def printList(self):
		current = self.head
		print "\nJOBS IN QUEUE:"
		print "%.4f----------------"%(MachineClass.CurrentTime)
		while (current != None):
			print "%s, class %s"%(current.job.name, current.job.priorityClass)
			current = current.nextNode
		




#----------------------------------------------------------------------#
# Class: JobClass
#
# This class is used to define jobs.
#
# Attributes: arrival time, processing time, remaining processing 
# time, estimated remaining processing time, percent error
#----------------------------------------------------------------------#
class JobClass(object):
	def __init__(self, master):
		self.master = master
		self.arrivalTime = 0
		self.procTime = 0
		self.RPT = 0		# Real Remaining Processing Time
		self.ERPT = 0		# Estimated Remaining Processing Time
		self.priorityClass = 100
		self.percentError = 0

	# Dictionary of service distributions
	def setServiceDist(self, procRate, procDist):
		ServiceDistributions =  {
			'Poisson': random.expovariate(1.0/procRate),
			'Exponential': random.expovariate(procRate),
			'Uniform': random.uniform(0.0, procRate),
			'Custom': self.setCustomDist
		}
		return ServiceDistributions[procDist]

	def setCustomDist(self, procRate):
		if main.timesClicked == 0:
			main.timesClicked += 1
			self.popup=CustomDist(self.master)
			self.master.wait_window(self.popup.top)
			main.customEquation = self.popup.stringEquation
		return eval(main.customEquation)

	# Generates a percent error for processing time
	def generateError(self, percError):
		self.percentError = pow(-1, random.randint(0,1)) * (percError * random.random())
		return self.percentError

	# Sets all processing times for job
	def setJobAttributes(self, procRate, procDist, percError, jobArrival):
		self.procTime = self.setServiceDist(procRate, procDist)
		self.estimatedProcTime = (1 + (self.generateError(percError)/100.0))*self.procTime
		self.RPT = self.procTime
		self.ERPT = self.estimatedProcTime
		self.arrivalTime = jobArrival


#----------------------------------------------------------------------#
# Class: MachineClass
#
# This class is used to generate Jobs at random and process them.
#
# Entities: jobs, server
# Events: job arrives, job completes
# Activities: processing job, waiting for new job
#
#----------------------------------------------------------------------#
class MachineClass(object):
	Queue = LinkedList()
	PreviousJobs = []
	JobOrderOut = []
	CurrentTime = 0.0
	NextArrival = 0.0
	ServiceStartTime = 0
	ServiceFinishTime = 0
	NumJobsInSys = 0
	ServerBusy = False
	JobInService = None

	def __init__(self, master):
		self.master = master
		MachineClass.Queue.clear()
		MachineClass.PreviousJobs[:] = []
		MachineClass.CurrentTime = 0.0
		MachineClass.NextArrival = 0.0
		MachineClass.ServiceStartTime = 0
		MachineClass.ServiceFinishTime = 0
		MachineClass.NumJobsInSys = 0
		MachineClass.ServerBusy = False
		MachineClass.JobInService = None

		NumJobs[:] = []
		TimeSys[:] = []
		ProcTime[:] = []
		PercError[:] = [] 
		MachineClass.JobOrderOut[:] = []
	
		self.ctr = 0

	# Dictionary of arrival distributions
	def setArrivalDist(self, arrRate, arrDist):
		ArrivalDistributions = {
			'Poisson': random.expovariate(1.0/arrRate),
			'Exponential': random.expovariate(arrRate)
			#'Normal': Rnd.normalvariate(self.inputInstance.valuesList[0])
			#'Custom':
		}
		return ArrivalDistributions[arrDist]
	
	def getProcessingJob(self):
		#if(MachineClass.Queue.Size > 0):
		currentJob = MachineClass.Queue.head.job
		return currentJob
		
		#else:
		#	GUI.writeToConsole(self.master, "nothing in queue")

	#update data
	def updateJob(self):
		currentJob = self.getProcessingJob()
		serviceTime = MachineClass.CurrentTime - MachineClass.ServiceStartTime
		currentJob.RPT -= serviceTime
		currentJob.ERPT -= serviceTime

	def saveArrivals(self, job):
		text = "%s,       %.4f,      %.4f,      %.4f,      %s"%(job.name, job.arrivalTime, job.RPT, job.ERPT, job.priorityClass) + "\n"
        
		with open("Arrivals.txt", "a") as myFile:
			myFile.write(text)
		myFile.close()

	# Give arriving job a class and add it to the queue
	def assignClass(self, numClasses, job):
		# Remove oldest job from previous jobs list if there are too many
		while len(MachineClass.PreviousJobs) > (numClasses - 1):
			MachineClass.PreviousJobs.pop(0)

		# Sort previous current job with previous jobs
		self.SortedPrevJobs = []
		self.SortedPrevJobs = list(MachineClass.PreviousJobs) 	# copy of prev jobs
		self.SortedPrevJobs.append(job)							# append current job (not a copy)
		self.SortedPrevJobs.sort(key=lambda JobClass: JobClass.ERPT)

		counter = 1
		for j in self.SortedPrevJobs:
			if j.name == job.name:
				job.priorityClass = counter
			counter += 1

		#GUI.writeToConsole(self.master, "------------------")
		#for j in self.SortedPrevJobs:
		#	GUI.writeToConsole(self.master, "%s, class %s"%(j.name, j.priorityClass))
		#GUI.writeToConsole(self.master, "------------------")

		# Add current job with new class to queue
		MachineClass.Queue.insert(job)			# add job to queue
		MachineClass.PreviousJobs.append(job)	# add job to previous jobs queue

		#MachineClass.Queue.printList() # print what is left in queue


	# Job arriving
	def arrivalEvent(self, arrRate, arrDist, procRate, procDist, numClasses, percError):
		J = JobClass(self.master)
		J.setJobAttributes(procRate, procDist, percError, MachineClass.CurrentTime)
		J.name = "Job%02d"%self.ctr
		self.ctr += 1

		MachineClass.NumJobsInSys += 1

		if(MachineClass.Queue.Size > 0):
			self.updateJob()	# update data in queue	

		self.assignClass(numClasses, J)			# give job a class, and add to queue

		GUI.writeToConsole(self.master, "%.6f | %s arrived, class = %s"%(MachineClass.CurrentTime, J.name, J.priorityClass))

		self.saveArrivals(J)					# save to list of arrivals, for testing
		self.processJob()						# process first job in queue

		MachineClass.NextArrival = MachineClass.CurrentTime + self.setArrivalDist(arrRate, arrDist) # generate next arrival

	# Processing first job in queue
	def processJob(self):
		MachineClass.ServiceStartTime = MachineClass.CurrentTime
		MachineClass.JobInService = self.getProcessingJob()
		MachineClass.ServiceFinishTime = MachineClass.CurrentTime + MachineClass.JobInService.RPT
		GUI.writeToConsole(self.master, "%.6f | %s processing, class = %s"%(MachineClass.CurrentTime, MachineClass.JobInService.name, MachineClass.JobInService.priorityClass))
		MachineClass.ServerBusy = True

		#MachineClass.Queue.removeHead() # remove job from queue

	# Job completed
	def completionEvent(self):
		GUI.writeToConsole(self.master, "%.6f | %s COMPLTED"%(MachineClass.CurrentTime, MachineClass.JobInService.name))

		MachineClass.JobOrderOut.append(MachineClass.JobInService.name)
		MachineClass.NumJobsInSys -= 1
		NumJobs.append(MachineClass.NumJobsInSys)
		TimeSys.append(MachineClass.CurrentTime - MachineClass.JobInService.arrivalTime)
		ProcTime.append(MachineClass.JobInService.procTime)
		PercError.append(abs(MachineClass.JobInService.percentError))

		MachineClass.ServerBusy = False
		MachineClass.JobInService = None

		MachineClass.Queue.removeHead() # remove job from queue

		#MachineClass.Queue.printList() 	# print what is left in queue
		


	def run(self, arrRate, arrDist, procRate, procDist, percError, numClasses, simLength):
		while 1:
			# Generate time of first job arrival
			if(self.ctr == 0):
				MachineClass.NextArrival = MachineClass.CurrentTime + self.setArrivalDist(arrRate, arrDist)

			# If no jobs in system, or time to arrival is less than remaining processing time of job currently processing
			if (MachineClass.ServerBusy == False) or ((MachineClass.ServerBusy == True) and (MachineClass.NextArrival < MachineClass.ServiceFinishTime)):
				#next event is arrival
				MachineClass.CurrentTime = MachineClass.NextArrival

				# stop server from processing current job
				self.ServerBusy == False

				self.arrivalEvent(arrRate, arrDist, procRate, procDist, numClasses, percError)

			else:
				#next event is job finishing
				MachineClass.CurrentTime = MachineClass.ServiceFinishTime
				self.completionEvent()

				if(MachineClass.Queue.Size > 0):
					self.processJob()

			# If current time is greater than the simulation length, end program
			if MachineClass.CurrentTime > simLength:
				break



#----------------------------------------------------------------------#
def main():
	window = GUI(None)                              # instantiate the class with no parent (None)
	window.title('Single Server SRPT with Errors')  # title the window

	# Global variables used in JobClass
	main.timesClicked = 0       
	main.customEquation = ""

	#window.geometry("500x600")                     # set window size
	window.mainloop()                               # loop indefinitely, wait for events


if __name__ == '__main__': main()
