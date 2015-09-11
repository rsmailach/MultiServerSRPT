#----------------------------------------------------------------------#
# SRPTE_SimPy3.py
#
# This application simulates a single server with Poisson arrivals
# and processing times of a general distribution. There are errors in
# time estimates within a range. Jobs are serviced in order of shortest 
# remaining processing time.
#
# Rachel Mailach
#----------------------------------------------------------------------#

#import simpy 
from Tkinter import *
from datetime import datetime
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
		self.frameIn.pack(side=TOP, fill=BOTH, padx = 5, pady =5, ipadx = 5, ipady = 5)     

		# Create the output frame
		self.frameOut = Output(self)
		self.frameOut.pack(side=TOP, fill=BOTH, padx = 5, pady =5, ipadx = 5, ipady = 5)

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
		consoleFrame.pack(side=TOP, padx=5, pady=5)
		self.console = Text(consoleFrame, wrap = WORD)
		self.console.config(state=DISABLED)     # start with console as disabled (non-editable)
		scrollbar = Scrollbar(consoleFrame)
		scrollbar.config(command = self.console.yview)
		self.console.config(yscrollcommand=scrollbar.set)
		self.console.grid(column=0, row=0)
		scrollbar.grid(column=1, row=0, sticky='NS')

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

	# Empty queue file at the begining of each simulation
	def clearQueueFile(self):
		open('Queue.txt', 'w').close()

	# Empty arrivals file at the begining of each simulation
	def clearSavedArrivals(self):
		with open("Arrivals.txt", "w") as myFile:
			myFile.write('Job Name, Req Processing Time, Est Processing Time' + '\n')
			myFile.close()

	def clearConsole(self, event):
		self.console.config(state=NORMAL)       # make console editable
		self.console.delete('1.0', END)
		self.console.config(state=DISABLED)     # disable (non-editable) console

	def updateStatusBar(self, text=' '):
		self.statusText.set(text)
	
	def printIntro(self):
		self.writeToConsole("SRPTE \n\n This application simulates a single server with Poisson arrivals and processing times of a general distribution. Each arrival has an estimation error within a percent error taken as input. Jobs are serviced in order of shortest remaining processing time.")

	def printParams(self, arrRate, procRate, percError, simLength): 
		self.writeToConsole("--------------------------------------------------------------------------------")
		self.writeToConsole("PARAMETERS:")
		self.writeToConsole("Arrival Rate = %.4f"%arrRate)
		self.writeToConsole("Processing Rate = %.4f"%procRate)
		self.writeToConsole("% Error  = " + u"\u00B1" + " %.4f"%percError)
		self.writeToConsole("Simulation Length = %.4f\n\n"%simLength)

	def calcVariance(self, List, avg):
		var = 0
		for i in List:
			var += (avg - i)**2
		return var/len(List)

	def displayAverageData(self):
		AvgNumJobs = int(float(sum(NumJobs))/len(NumJobs))
		AvgTimeSys = float(sum(TimeSys))/len(TimeSys)
		AvgProcTime = float(sum(ProcTime))/len(ProcTime)
		VarProcTime = self.calcVariance(ProcTime, AvgProcTime)
		AvgPercError = float(sum(PercError))/len(PercError)

		self.writeToConsole('\n\nAverage number of jobs in the system %s' %AvgNumJobs)
		self.writeToConsole('Average time in system, from start to completion is %s' %AvgTimeSys)
		self.writeToConsole('Average processing time, based on generated service times is %s' %AvgProcTime)
		self.writeToConsole('Variance of processing time %s' %VarProcTime)
		self.writeToConsole('Average percent error %.4f\n' %AvgPercError)
		#self.writeToConsole('Request order: %s' % ArrivalClass.JobOrderIn)
		self.writeToConsole('Service order: %s\n\n' % MachineClass.JobOrderOut)
		self.writeToConsole("--------------------------------------------------------------------------------")
		self.writeToConsole('NOTE: THERE ARE STILL ERRORS WHEN RUNING MULTIPLE SIMULATIONS WITHOUT FIRST QUITTING THE APPLICATION.')
		self.writeToConsole("--------------------------------------------------------------------------------\n\n\n")

				
	def submit(self, event):
		self.updateStatusBar("Simulating...")
		self.clearQueueFile()
		self.clearSavedArrivals()
		inputInstance = Input(self)     

		self.printParams(inputInstance.valuesList[0], inputInstance.valuesList[1],\
				 inputInstance.valuesList[2], inputInstance.valuesList[3])

		main.timesClicked = 0
		
		# Start process
		MC = MachineClass(self)
		MC.run(inputInstance.valuesList[0], 'Poisson',\
				inputInstance.valuesList[1], inputInstance.distList[1],\
				inputInstance.valuesList[2], inputInstance.valuesList[3])

		#self.displayAverageData()
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
		self.simLengthInput = DoubleVar()
		self.errorMessage = StringVar()

		self.arrivalRateInput.set(2.0)          ##################################CHANGE LATER
		self.processingRateInput.set(0.5)       ##################################CHANGE LATER
		self.percentErrorInput.set(20)          ##################################CHANGE LATER
		self.simLengthInput.set(50.0)           ##################################CHANGE LATER

		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(0, weight=1)

		# Labels
		labels = ['Interarrival Rate (' + u'\u03bb' + ')', 'Processing Rate (' + u'\u03bc' + ')', '% Error' , 'Simulation Length']
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
		self.entry_4 = Entry(self, textvariable = self.simLengthInput)
		self.entry_1.grid(row = 0, column = 2)
		self.entry_2.grid(row = 1, column = 2)
		self.entry_3.grid(row = 2, column = 2)
		self.entry_4.grid(row = 3, column = 2)


		# Distribution Dropdowns
		self.distributions = ('Select Distribution', 'Exponential', 'Uniform', 'Custom')
		#self.comboBox_1 = ttk.Combobox(self, values = self.distributions, state = 'readonly')
		#self.comboBox_1.current(0) # set selection
		#self.comboBox_1.grid(row = 0, column = 2)
		self.comboBox_2 = ttk.Combobox(self, values = self.distributions, state = 'readonly')
		self.comboBox_2.current(1) # set default selection                  #####################CHANGE LATER
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
		if maxSimLength <= 0.0:
				self.errorMessage.set("Simulation length must be non-zero value!")
				return 1
		else:
				self.errorMessage.set("")
				Input.valuesList = [arrivalRate, processingRate, percentError, maxSimLength]
				return 0

	def getDropDownValues(self):
		#if self.comboBox_1.get() == 'Select Distribution': print "Box 1 has to have a selection"
		comboBox2Value = self.comboBox_2.get()
		if comboBox2Value == 'Select Distribution':
				self.errorMessage.set("You must select a distribution for the processing rate")
				return 1
		else:
				self.errorMessage.set("")
				Input.distList = ["", comboBox2Value, "", "", ""]
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

	# ................................... COPIED DIRECTLY ...................................
	# http://stackoverflow.com/questions/28464077/insert-in-ordered-linked-list-python
	def printQueue(self):
		data_list = []    
		current = self.head
		while current is not None:
			data_list.append(str(current.data))
			current = current.next
		return '->'.join(data_list)
    # ................................... COPIED DIRECTLY ...................................

    # Insert job into queue (sorted by ERPT)
	def insert(self, job):
		current = self.head		# node iterator, starts at head
		previous = None
		if (current == None):	# if queue is empty, set current job as head
			self.head = Node(job, None)
		else:
			while (current != None) and (job.ERPT > current.job.ERPT):
				previous = current 				# prev = node[i]
				current = current.nextNode 		# current = node[i+1]
			


			# Insert new node after previous before current
			if(previous == None):
				self.head = Node(job, current)
			else:
				previous.nextNode = Node(job, current)

		LinkedList.Size += 1

	# Remove first item in queue
	def remove(self):
		if (LinkedList.Size > 0):
			self.head = self.head.nextNode		# move head forward one node
			LinkedList.Size -= 1
		else:
			GUI.writeToConsole(self.master, "ERROR: The linked list is already empty!")


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
		self.percentError = 0

	# Dictionary of service distributions
	def setServiceDist(self, procRate, procDist):
		self.ServiceDistributions =  {
			'Exponential': self.setExponDist,
			'Uniform': self.setUniformDist,
			#'Normal': Rnd.normalvariate(self.ServiceRate)
			'Custom': self.setCustomDist
		}
		return self.ServiceDistributions[procDist](procRate)

	def setExponDist(self, procRate):
		return random.expovariate(procRate)

	def setUniformDist(self, procRate):
		return random.uniform(0.0, procRate)

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
	JobOrderOut = []
	CurrentTime = 0.0
	ServiceStartTime = 0
	NumJobsInSys = 0

	def __init__(self, master):
		self.master = master
		self.timeUntilArrival = 0.0
		self.timeOfArrival = 0.0
		self.serverBusy = False

		NumJobs = []
		TimeSys = []
		ProcTime = []
		PercError = [] 
	
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
	
	def enqueueJob(self, job):
		MachineClass.Queue.insert(job)

	def dequeueJob(self):
		pass

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

	# Job arriving
	def arrivalEvent(self, arrRate, arrDist, procRate, procDist, percError):
		J = JobClass(self.master)
		J.setJobAttributes(procRate, procDist, percError, MachineClass.CurrentTime)
		J.name = "Job%02d"%self.ctr
		self.ctr += 1

		MachineClass.NumJobsInSys += 1

		GUI.writeToConsole(self.master, "%.6f | %s arrived, ERPT = %.5f"%(MachineClass.CurrentTime, J.name, J.ERPT))
		if(MachineClass.Queue.Size > 0):
			self.updateJob()	# update data in queue
		self.enqueueJob(J)	# add job to queue
		self.processJob()	# process first job in queue

		self.timeUntilArrival = self.setArrivalDist(arrRate, arrDist) # generate next arrival
		self.timeOfArrival = MachineClass.CurrentTime + self.timeUntilArrival

	# Processing first job in queue
	def processJob(self):
		MachineClass.ServiceStartTime = MachineClass.CurrentTime
		currentJob = self.getProcessingJob()
		GUI.writeToConsole(self.master, "%.6f | %s processing, ERPT = %.5f"%(MachineClass.CurrentTime, currentJob.name, currentJob.ERPT))
		self.serverBusy = True

	# Job completed
	def completionEvent(self):
		currentJob = self.getProcessingJob()
		GUI.writeToConsole(self.master, "%.6f | %s COMPLTED"%(MachineClass.CurrentTime, currentJob.name))

		self.serverBusy = False

		MachineClass.JobOrderOut.append(currentJob.name)
		MachineClass.NumJobsInSys -= 1
		NumJobs.append(MachineClass.NumJobsInSys)
		TimeSys.append(MachineClass.CurrentTime - currentJob.arrivalTime)
		ProcTime.append(currentJob.procTime)
		PercError.append(abs(currentJob.percentError))


		self.dequeueJob() # remove job from queue
		


	def run(self, arrRate, arrDist, procRate, procDist, percError, simLength):
		while 1:
			# If no jobs in system, or time to arrival is less than remaining processing time of job currently processing
			if (self.serverBusy == False) or ((self.serverBusy == True) and (self.timeUntilArrival < self.getProcessingJob().RPT)):
				#next event is arrival
				MachineClass.CurrentTime += self.timeUntilArrival

				# stop server from processing current job
				self.serverBusy == False
				self.arrivalEvent(arrRate, arrDist, procRate, procDist, percError)
			else:
				#next event is job finishing
				MachineClass.CurrentTime += self.getProcessingJob().RPT
				self.completionEvent()

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
