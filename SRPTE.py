#----------------------------------------------------------------------#
# SRPTE.py
#
# This application simulates a single server with Poisson arrivals
# and processing times of a general distribution. There are errors in
# time estimates within a range. Jobs are serviced in order of shortest 
# remaining processing time.
#
# Rachel Mailach
#----------------------------------------------------------------------#

from Tkinter import *
from datetime import datetime
from math import log
import plotly.plotly as py
from plotly.graph_objs import Scatter
import plotly.graph_objs as go
#from scipy import integrate as integrate
import copy
import random
import tkMessageBox
import ttk
import tkFileDialog
import csv
import operator

NumJobs = []
NumJobsTime = []
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
		self.consoleFrame = Frame(self.frameOut)
		self.console = Text(self.consoleFrame, wrap = WORD)		
		self.makeConsole()
		self.printIntro()
		self.updateStatusBar("Waiting for submit...")

	def makeConsole(self):
		#self.consoleFrame = Frame(self.frameOut)
		self.consoleFrame.pack(side=TOP, padx=5, pady=5)
		#self.console = Text(self.consoleFrame, wrap = WORD)
		self.console.config(state=DISABLED)     # start with console as disabled (non-editable)
		self.scrollbar = Scrollbar(self.consoleFrame)
		self.scrollbar.config(command = self.console.yview)
		self.console.config(yscrollcommand=self.scrollbar.set)
		self.console.grid(column=0, row=0)
		self.scrollbar.grid(column=1, row=0, sticky='NS')

	def writeToConsole(self, text = ' '):
		self.console.config(state=NORMAL)       # make console editable
		self.console.insert(END, '%s\n'%text)
		self.update()
		self.console.yview(END)					# auto-scroll
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
			myFile.write('Job Name,      Arrival Time,      RPT,       ERPT' + '\n')
			myFile.close()

	def clearConsole(self, event):
		self.console.config(state=NORMAL)       # make console editable
		self.console.delete('1.0', END)
		self.console.config(state=DISABLED)     # disable (non-editable) console

	def updateStatusBar(self, text=' '):
		self.statusText.set(text)
	
	def printIntro(self):
		self.writeToConsole("SRPTE \n\n This application simulates a single server with Poisson arrivals and processing times of a general distribution. Each arrival has an estimation error within a percent error taken as input. Jobs are serviced in order of shortest remaining processing time.")

	def printParams(self, load, arrDist, procRate, procDist, percError, simLength): 
		self.writeToConsole("--------------------------------------------------------------------------------")
		self.writeToConsole("PARAMETERS:")
		self.writeToConsole("Load = %.4f"%load)
		#self.writeToConsole("Arrival Rate = %.4f"%arrRate)
		self.writeToConsole("Arrival Distribution = %s"%arrDist)
		self.writeToConsole("Processing Rate = %.4f, Processing Distribution = %s"%(procRate, str(procDist)))
		self.writeToConsole("% Error  = " + u"\u00B1" + " %.4f"%percError)
		self.writeToConsole("Simulation Length = %.4f\n\n"%simLength)


	def plotNumJobsInSys(self):
		py.sign_in('mailacrs','wowbsbc0qo')
		trace0 = Scatter(x=NumJobsTime, y=NumJobs)
		data = [trace0]
		layout = go.Layout(
			title='Average Number of Jobs Over Time',
			xaxis=dict(
				title='Time',
				titlefont=dict(
				family='Courier New, monospace',
				size=18,
				color='#7f7f7f'
			)
		),
			yaxis=dict(
				title='Number of Jobs',
				titlefont=dict(
				family='Courier New, monospace',
				size=18,
				color='#7f7f7f'
			)
		)
		)
		fig = go.Figure(data=data, layout=layout)
		unique_url = py.plot(fig, filename = 'SRPT_NumJobsInSys: Case1')


	def calcVariance(self, List, avg):
		var = 0
		for i in List:
			var += (avg - i)**2
		return var/len(List)

	def displayAverageData(self):
		self.plotNumJobsInSys()
		##AvgNumJobs = int(float(sum(NumJobs))/len(NumJobs))
		AvgNumJobs = MachineClass.AvgNumJobs
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


	def submit(self, event):
		self.updateStatusBar("Simulating...")
		self.clearSavedArrivals()
		I = Input(self)     

		self.printParams(I.valuesList[0], 					#load
						 'Exponential',						#arrival
						 I.valuesList[1], I.distList[1],	#processing rate
						 I.valuesList[2], 					#error
						 I.valuesList[3])					#sim time

		main.timesClicked = 0
		
		# Start process
		MC = MachineClass(self)
		MC.run(	I.valuesList[0],				# load 
				'Exponential',					# arrival
				I.valuesList[1], I.distList[1],	# processing
				I.valuesList[2], 				# error
				I.valuesList[3])				# sim time

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
		self.loadInput = DoubleVar()
		self.arrivalRateInput = DoubleVar()
		self.processingRateInput = DoubleVar()
		self.percentErrorInput = DoubleVar()
		self.simLengthInput = DoubleVar()
		self.errorMessage = StringVar()
		self.comboboxVal = StringVar()

		self.loadDefault = 0.8					##################################CHANGE LATER	
		#self.arrRateDefault = 0.8				##################################CHANGE LATER
		self.procRateDefault = 0.5				##################################CHANGE LATER

		self.loadInput.set(self.loadDefault)
		#self.arrivalRateInput.set(self.arrRateDefault)
		self.processingRateInput.set(self.procRateDefault)
		self.percentErrorInput.set(20)
		self.simLengthInput.set(10000.0)

		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(0, weight=1)

		# Labels
		labels = ['System Load', 'Interarrival Rate (' + u'\u03bb' + ')', 'Processing Rate (' + u'\u03bc' + ')', '% Error' , 'Simulation Length']
		r=0
		c=0
		for elem in labels:
			Label(self, text=elem).grid(row=r, column=c)
			r=r+1
		
		Label(self, textvariable=self.errorMessage, fg="red", font=14).grid(row=6, columnspan=4) #error message, invalid input
		Label(self, text=u"\u00B1").grid(row=3, column=1) # +/-

		# Entry Boxes
		self.entry_0 = Entry(self, textvariable = self.loadInput)
		self.entry_1 = Entry(self, textvariable = self.arrivalRateInput)
		self.entry_2 = Entry(self, textvariable = self.processingRateInput)
		self.entry_3 = Entry(self, textvariable = self.percentErrorInput)
		self.entry_4 = Entry(self, textvariable = self.simLengthInput)
		self.entry_0.grid(row = 0, column = 2)
		self.entry_1.grid(row = 1, column = 2)
		self.entry_2.grid(row = 2, column = 2)
		self.entry_3.grid(row = 3, column = 2)
		self.entry_4.grid(row = 4, column = 2)
		

		# Disable interarrival time
		self.entry_1.delete(0, 'end')
		self.entry_1.configure(state = 'disabled')

		# Swaps between load and interrarival rate based on input
		#self.loadInput.trace('w', self.entryBoxChange)
		#self.arrivalRateInput.trace('w', self.entryBoxChange)
		#self.refreshLoad()


		# Distribution Dropdowns
		self.distributions = ('Select Distribution', 'Poisson', 'Exponential', 'Uniform', 'Bounded Pareto', 'Custom')
		self.comboBox_1 = ttk.Combobox(self, values = self.distributions, state = 'disabled')
		self.comboBox_1.current(2) # set selection
		self.comboBox_1.grid(row = 1, column = 3)
		self.comboBox_2 = ttk.Combobox(self, textvariable = self.comboboxVal, values = self.distributions, state = 'readonly')
		self.comboBox_2.current(4) # set default selection                  #####################CHANGE LATER
		self.comboBox_2.grid(row = 2, column = 3)

		self.comboboxVal.trace("w", self.selectionChange) # refresh on change
		self.refreshComboboxes()

		# Simulate Button
		self.simulateButton = Button(self, text = "SIMULATE", command = self.onButtonClick)
		self.simulateButton.grid(row = 7, columnspan = 4)

	def entryBoxChange(self, name, index, mode):
		self.refreshLoad()

	def refreshLoad(self):
		if len(self.entry_0.get()) > 0:
			self.entry_1.delete(0, 'end')
			self.entry_1.configure(state = 'disabled')
		else:
			self.entry_1.configure(state = 'normal')
			self.arrivalRateInput.set(self.arrRateDefault)

		if len(self.entry_1.get()) > 0:
			self.entry_0.delete(0, 'end')
			self.entry_0.configure(state = 'disabled')
		else:
			self.entry_0.configure(state = 'normal')
			self.loadInput.set(self.loadDefault)

	def selectionChange(self, name, index, mode):
		self.refreshComboboxes()

	def refreshComboboxes(self):
		selection = self.comboBox_2.get()
		if selection == 'Bounded Pareto':
			#self.entry_2.delete(0, 'end')
			self.entry_2.configure(state = 'disabled')
		else:
			self.entry_2.configure(state = 'normal')
			#self.processingRateInput.set(self.procRateDefault)

	def onButtonClick(self):
		if (self.getNumericValues() == 0) and (self.getDropDownValues() == 0):
				# Send to submit button in main 
				self.simulateButton.event_generate("<<input_simulate>>")

	def getNumericValues(self):
		try:
			load = self.loadInput.get()
			#arrivalRate = self.arrivalRateInput.get()
			processingRate = self.processingRateInput.get()
			percentError = self.percentErrorInput.get()
			maxSimLength = self.simLengthInput.get()
		except ValueError:
				self.errorMessage.set("One of your inputs is an incorrect type, try again.")
				return 1

		if load <= 0.0:
			self.errorMessage.set("System load must be a non-zero value!")
			return 1
		#if arrivalRate <= 0.0:
		#	self.errorMessage.set("Arrival rate must be a non-zero value!")
		#	return 1
		if processingRate <= 0.0:
			self.errorMessage.set("Processing rate must be a non-zero value!")
			return 1
		if maxSimLength <= 0.0:
			self.errorMessage.set("Simulation length must be a non-zero value!")
			return 1
		else:
			self.errorMessage.set("")
			Input.valuesList = [load, processingRate, percentError, maxSimLength]
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

		self.x=Button(frame2, text="x", command=self.insertX)
		self.x.pack(side=LEFT)

		self.ln=Button(frame2, text="ln", command=self.insertLn)
		self.ln.pack(side=LEFT)

		# Input frame
		frame3 = Frame(top)
		frame3.pack(side=TOP, padx=5, pady=5)
		self.e = Entry(frame3, textvariable = self.function)
		self.e.insert(0, "-ln(1 - x)/" + u'\u03bc')
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

	def insertX(self):
		self.e.insert(END, "x")

	def insertLn(self):
		self.e.insert(END, "ln")

	def convertFunction(self):
		self.stringList = list(self.e.get())
		for i in range(len(self.stringList)):
			if self.stringList[i] == u'\u03bc':
				self.stringList[i] = "procRate"
			elif self.stringList[i] == "x":
				self.stringList[i] = "random.uniform(0.0, 1.0)"
			elif self.stringList[i] == "l" and self.stringList[i+1] == "n":
				self.stringList[i] = "log"
				self.stringList[i+1] = ""
		print "".join(self.stringList)
		return "".join(self.stringList)

#----------------------------------------------------------------------#
# Class: BoundedParetoDist
#
# This class is used to allow users to enter parameters to 
# Bounded Pareto distribution.
#
#----------------------------------------------------------------------#
class BoundedParetoDist(object):
	Array = []
	def __init__(self, master):
		top = self.top = Toplevel(master)
		top.geometry("500x200")                     # set window size
		top.resizable(0,0)
		
		self.errorMessage = StringVar()

		self.alpha = DoubleVar()
		self.L = DoubleVar()
		self.U = DoubleVar()

		# Set default parameters
		self.alpha.set(1.1)
		self.L.set(1)
		self.U.set(10**(6))

		# Label frame
		frame1 = Frame(top)
		frame1.pack(side=TOP, padx=5, pady=5)
		self.l=Label(frame1, text="Please enter the parameters you would like.", font=("Helvetica", 12), justify=LEFT)
		self.l.pack()
		self.error = Label(frame1, textvariable=self.errorMessage, fg="red", font=14)
		self.error.pack()

		# Input frame
		frame2 = Frame(top)
		frame2.pack(side=TOP, padx=5, pady=5)

		frame2.grid_columnconfigure(0, weight=1)
		frame2.grid_rowconfigure(0, weight=1)

		self.l1 = Label(frame2, text = "alpha (shape)")
		self.l2 = Label(frame2, text = "L (smallest job size)")
		self.l3 = Label(frame2, text = "U (largest job size)")
		self.l1.grid(row = 0, column = 0)
		self.l2.grid(row = 1, column = 0)
		self.l3.grid(row = 2, column = 0)

		self.e1 = Entry(frame2, textvariable = self.alpha)
		self.e2 = Entry(frame2, textvariable = self.L)		
		self.e3 = Entry(frame2, textvariable = self.U)		
		self.e1.grid(row = 0, column = 1)
		self.e2.grid(row = 1, column = 1)
		self.e3.grid(row = 2, column = 1)		

		frame3 = Frame(top)
		frame3.pack(side=TOP, pady=10)
		self.b=Button(frame3,text='Ok',command=self.cleanup)
		self.b.pack()

	def cleanup(self):
		if(self.checkParams() == 0):
			self.paramArray=BoundedParetoDist.Array
			self.top.destroy()

	def checkParams(self):
		self.a = float(self.e1.get())
		self.l = float(self.e2.get())
		self.u = float(self.e3.get())
		if (self.a <= 0) or (self.u < self.l) or (self.l <= 0):
			print "ERROR: Bounded pareto paramater error"
			self.errorMessage.set("Bounded pareto paramater error")
			return 1
		else:
			self.errorMessage.set("")
			BoundedParetoDist.Array = [self.a, self.l, self.u]
			return 0


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
		self.head = None

	def printList(self):
		current = self.head
		while (current != None):
			print current.job.name, current.job.ERPT
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
	BPArray = []

	def __init__(self, master):
		self.master = master
		self.arrivalTime = 0
		self.procTime = 0
		self.RPT = 0		# Real Remaining Processing Time
		self.ERPT = 0		# Estimated Remaining Processing Time
		self.percentError = 0
		self.processRate = 0
		self.arrivalRate = 0
		#JobClass.BPArray = []

	def setArrProcRates(self, load, procRate, procDist):
		if procDist == 'Bounded Pareto':
			alpha = JobClass.BPArray[0]
			L = JobClass.BPArray[1]
			U = JobClass.BPArray[2]
			if alpha > 1 and L > 0:
				procMean = (L**alpha/(1 - (L/U)**alpha))*(alpha/(alpha - 1))*((1/(L**(alpha - 1)))-(1/(U**(alpha - 1))))
				self.processRate = 1/float(procMean)
		else:
			self.processRate = procRate
		self.arrivalRate = float(load) * self.processRate

	# Dictionary of service distributions
	def setServiceDist(self, procRate, procDist):
		ServiceDistributions =  {
			'Poisson': random.expovariate(1.0/procRate),
			'Exponential': random.expovariate(procRate),
			'Uniform': random.uniform(0.0, procRate),
			'Bounded Pareto': self.setBoundedPareto,
			'Custom': self.setCustomDist
		}
		if(procDist == 'Custom'):
			return ServiceDistributions[procDist](procRate)
		elif(procDist == 'Bounded Pareto'):
			return ServiceDistributions[procDist]()
		else:
			return ServiceDistributions[procDist]

	def setCustomDist(self, procRate):
		if main.timesClicked == 0:
			main.timesClicked += 1
			self.popup = CustomDist(self.master)
			self.master.wait_window(self.popup.top)
			main.customEquation = self.popup.stringEquation
		return eval(main.customEquation)

	def setBoundedPareto(self):
		# Get and set parameters (in job class array)
		if main.timesClicked == 0:
			main.timesClicked += 1
			self.popup = BoundedParetoDist(self.master)
			self.master.wait_window(self.popup.top)		
			self.alpha = float(self.popup.paramArray[0])	# Shape, power of tail, alpha = 2 is approx Expon., alpha = 1 gives higher variance
			self.L = float(self.popup.paramArray[1])		# Smallest job size
			self.U = float(self.popup.paramArray[2])		# Largest job size
			JobClass.BPArray = [self.alpha, self.L, self.U]

			
		x = random.uniform(0.0, 1.0)
		# reassigning 
		alpha = JobClass.BPArray[0]
		L = JobClass.BPArray[1]
		U = JobClass.BPArray[2]

		paretoNumerator = float(-(x*(U**alpha) - x*(L**alpha) - (U**alpha)))
		paretoDenominator = float((U**alpha) * (L**alpha))
		main.customEquation = (paretoNumerator/paretoDenominator)**(-1/alpha)
		
		return main.customEquation


	# Generates a percent error for processing time
	def generateError(self, percError):
		self.percentError = pow(-1, random.randint(0,1)) * (percError * random.random())
		return self.percentError

	# Sets all processing times for job
	def setJobAttributes(self, load, procRate, procDist, percError, jobArrival):
		if(procDist == 'Bounded Pareto'):
			self.procTime = self.setServiceDist(procRate, procDist) 		#use updated proc rate
			self.setArrProcRates(load, procRate, procDist)
		else:
			self.setArrProcRates(load, procRate, procDist)
			self.procTime = self.setServiceDist(procRate, procDist) 		#use updated proc rate
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
	TimeUntilArrival = 0.0
	ServiceStartTime = 0
	AvgNumJobs = 0
	PrevTime = 0
	PrevNumJobs = 0
	ServerBusy = False


	def __init__(self, master):
		self.master = master
		MachineClass.ServerBusy = False
		MachineClass.Queue.clear()
		LinkedList.Size = 0
		MachineClass.CurrentTime = 0.0
		MachineClass.TimeUntilArrival = 0.0
		MachineClass.ServiceStartTime = 0
		MachineClass.AvgNumJobs = 0
		MachineClass.PrevTime = 0
		MachineClass.PrevNumJobs = 0

		NumJobs[:] = []
		NumJobsTime[:] = []
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
		currentJob = MachineClass.Queue.head.job
		return currentJob

	#update data
	def updateJob(self):
		currentJob = self.getProcessingJob()
		serviceTime = MachineClass.CurrentTime - MachineClass.ServiceStartTime
		currentJob.RPT -= serviceTime
		currentJob.ERPT -= serviceTime

	def calcNumJobs(self, jobID):
		if(MachineClass.ServerBusy == True):
			self.currentNumJobs = MachineClass.Queue.Size + 1
		else:
			self.currentNumJobs = MachineClass.Queue.Size

		changeInJobs = MachineClass.PrevNumJobs - self.currentNumJobs
		self.t = MachineClass.CurrentTime
		self.delta_t = self.t - MachineClass.PrevTime 

		# If one job in system
		if(jobID == 0):
			MachineClass.AvgNumJobs = 1 # First event is always create new job
		# UPDATE 
		else:
			MachineClass.AvgNumJobs = (MachineClass.PrevTime/(self.t))*float(MachineClass.AvgNumJobs) + float(MachineClass.PrevNumJobs)*(float(self.delta_t)/self.t)
			
		# PrevTime becomes "old" t
		MachineClass.PrevTime = self.t 
		# PrevNum jobs becomes current num jobs
		MachineClass.PrevNumJobs = self.currentNumJobs


	# Job arriving
	def arrivalEvent(self, load, arrDist, procRate, procDist, percError):
		J = JobClass(self.master)
		J.setJobAttributes(load, procRate, procDist, percError, MachineClass.CurrentTime)
		J.name = "Job%02d"%self.ctr

		GUI.writeToConsole(self.master, "%.6f | %s arrived, ERPT = %.5f"%(MachineClass.CurrentTime, J.name, J.ERPT))
		self.calcNumJobs(self.ctr)
		self.saveArrivals(J)					# save to list of arrivals, for testing

		if(MachineClass.Queue.Size > 0):
			self.updateJob()	# update data in queue
		MachineClass.Queue.insert(J)	# add job to queue
		self.processJob()	# process first job in queue

		# Generate next arrival
		MachineClass.TimeUntilArrival = self.setArrivalDist(J.arrivalRate, arrDist)
		self.ctr += 1

	def insertLargeJob(self, procDist):
		J = JobClass(self.master)
		J.setJobAttributes(1, 1, procDist, 1, MachineClass.CurrentTime)
		J.name = "JobXXXXX"
		J.RPT = 10000
		J.ERPT = 1
		GUI.writeToConsole(self.master, "%.6f | %s arrived, ERPT = %.5f"%(MachineClass.CurrentTime, J.name, J.ERPT))
		
		MachineClass.Queue.insert(J)	# add job to queue

	def saveArrivals(self, job):
		text = "%s,       %.4f,      %.4f,      %.4f"%(job.name, job.arrivalTime, job.RPT, job.ERPT) + "\n"
		
		with open("Arrivals.txt", "a") as myFile:
			myFile.write(text)
		myFile.close()

	# Processing first job in queue
	def processJob(self):
		MachineClass.ServiceStartTime = MachineClass.CurrentTime
		currentJob = self.getProcessingJob()
		GUI.writeToConsole(self.master, "%.6f | %s processing, ERPT = %.5f"%(MachineClass.CurrentTime, currentJob.name, currentJob.ERPT))
		MachineClass.ServerBusy = True

	# Job completed
	def completionEvent(self):
		currentJob = self.getProcessingJob()
		MachineClass.ServerBusy = False

		MachineClass.JobOrderOut.append(currentJob.name)
		self.calcNumJobs(self.ctr)
		NumJobs.append(MachineClass.AvgNumJobs)			# y axis of plot
		NumJobsTime.append(MachineClass.CurrentTime)	# x axis of plot
		TimeSys.append(MachineClass.CurrentTime - currentJob.arrivalTime)
		ProcTime.append(currentJob.procTime)
		PercError.append(abs(currentJob.percentError))

		GUI.writeToConsole(self.master, "%.6f | %s COMPLTED"%(MachineClass.CurrentTime, currentJob.name))
		MachineClass.Queue.removeHead() # remove job from queue




	def run(self, load, arrDist, procRate, procDist, percError, simLength):
		has_run = False
		while 1:
			if(self.ctr == 0):	# set time of first job arrival
				arrRate = float(load) / procRate
				MachineClass.TimeUntilArrival = self.setArrivalDist(arrRate, arrDist) # generate next arrival

			# If no jobs in system, or time to arrival is less than remaining processing time of job currently processing
			if (MachineClass.CurrentTime >= 5000 and has_run == False):
				self.insertLargeJob(procDist)
				has_run = True

			elif (MachineClass.ServerBusy == False) or ((MachineClass.ServerBusy == True) and (MachineClass.TimeUntilArrival < self.getProcessingJob().RPT)):
				#next event is arrival
				MachineClass.CurrentTime += MachineClass.TimeUntilArrival

				# stop server from processing current job
				MachineClass.ServerBusy == False
				self.arrivalEvent(load, arrDist, procRate, procDist, percError)
			else:
				#next event is job finishing
				MachineClass.CurrentTime += self.getProcessingJob().RPT
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
