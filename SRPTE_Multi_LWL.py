#----------------------------------------------------------------------#
# SRPTE_Multi_LWL.py
#
# This application simulates multiple server with Poisson arrivals
# and processing times of a general distribution. There are errors in
# time estimates within a range. Jobs join the queue with shortest RPT and
# serviced in order of shortest remaining processing time.
#
# Rachel Mailach
#----------------------------------------------------------------------#

from Tkinter import *
from datetime import datetime
from math import log
import plotly.plotly as py
from plotly.graph_objs import Scatter
import plotly.graph_objs as go
from itertools import cycle

import copy
import random
import tkMessageBox
import ttk
import tkFileDialog
import csv
import operator

import sqlite3
import pandas

conn=sqlite3.connect('MultiServerDatabase_SRPTE_LWL.db')

NumJobs = []
NumJobsTime = []

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
		global SEED
		#SEED = random.randint(0, 1000000000)
		SEED = 994863731
		random.seed(SEED)

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

		# Bind stop button
		self.bind("<<stop_sim>>", self.stopSimulation)		

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

		#DOES NOTHING??
		self.grid_columnconfigure(0, weight=1) 
		self.grid_rowconfigure(0, weight=1)


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

	def printParams(self, load, arrDist, procRate, procDist, percErrorMin, percErrorMax, simLength): 
		self.writeToConsole("--------------------------------------------------------------------------------")
		self.writeToConsole("PARAMETERS:")
		self.writeToConsole("Number of Servers = %s"%NUM_SERVERS)
		self.writeToConsole("Load = %.4f"%load)
		#self.writeToConsole("Arrival Rate = %.4f"%arrRate)
		self.writeToConsole("Arrival Distribution = %s"%arrDist)
		self.writeToConsole("Processing Rate = %.4f, Processing Distribution = %s"%(procRate, str(procDist)))
		self.writeToConsole("% Error  = " + " %.4f, %.4f"%(percErrorMin, percErrorMax))
		self.writeToConsole("Simulation Length = %.4f\n\n"%simLength)

	def saveParams(self, load, arrRate, arrDist, procRate, procDist, percErrorMin, percErrorMax, simLength, alpha, lower, upper):
		params = pandas.DataFrame({	'seed' : [SEED],
									'numServers' : [NUM_SERVERS],
									'load' : [load],
									'arrRate' : [arrRate],
									'arrDist' : [arrDist],
									'procRate' : [procRate],
									'procDist' : [procDist],
									'alpha' : [alpha],
									'lower' : [lower],
									'upper' : [upper],
									'percErrorMin' : [percErrorMin],
									'percErrorMax' : [percErrorMax],
									'simLength' : [simLength],
									'avgNumJobs' : [MachineClass.AvgNumJobs],
									#'avgNumJobsClass' : [MachineClass.AvgNumJobsClass]
									})

		params.to_sql(name='parameters', con=conn, if_exists='append')
		print params

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
		unique_url = py.plot(fig, filename = 'SRPT_NumJobsInSys')

	def calcVariance(self, List, avg):
		var = 0
		for i in List:
			var += (avg - i)**2
		return var/len(List)

	def stopSimulation(self, event):
		MachineClass.StopSim = True
				
	def submit(self, event):
		self.updateStatusBar("Simulating...")
		self.clearSavedArrivals()
		I = Input(self)   

		# Set global variable for num servers to value inputed  
		global NUM_SERVERS
		NUM_SERVERS = I.valuesList[0]

		self.printParams(I.valuesList[1],					#load
						 'Exponential',						#arrival
						 I.valuesList[2], I.distList[1], 	#processing rate
						 I.valuesList[3],					#error min
						 I.valuesList[4],					#error max
						 I.valuesList[5])					#sim time

		main.timesClicked = 0
		
		# Start process
		MC = MachineClass(self)
		MC.run(	I.valuesList[1],				#load
				'Exponential',					#arrival
				I.valuesList[2], I.distList[1],	# proc
				I.valuesList[3],				# error min
				I.valuesList[4],				# error max
				I.valuesList[5])				# sim time

		self.saveParams(I.valuesList[1],		#load
					'?', 						# arrival rate
					'Exponential',					# arrival dist
					'?', I.distList[1],	# processing
					I.valuesList[3], 				# error min
					I.valuesList[4],				# error max
					I.valuesList[5],				# sim time
					JobClass.BPArray[0],			# alpha
					JobClass.BPArray[1],			# lower
					JobClass.BPArray[2])			# upper				

		self.plotNumJobsInSys()
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
		self.numServersInput = IntVar()
		self.loadInput = DoubleVar()
		self.arrivalRateInput = DoubleVar()
		self.processingRateInput = DoubleVar()
		self.percentErrorMinInput = DoubleVar()
		self.percentErrorMaxInput = DoubleVar()
		self.simLengthInput = DoubleVar()
		self.errorMessage = StringVar()
		self.comboboxVal = StringVar()

		self.numServersInput.set(2)					##################################CHANGE LATER	
		self.loadInput.set(0.90)       		 	   	##################################CHANGE LATER
		#self.arrivalRateInput.set(1.0)         	 ##################################CHANGE LATER
		self.processingRateInput.set(0.5)   	    ##################################CHANGE LATER
		self.percentErrorMinInput.set(-50)          ##################################CHANGE LATER
		self.percentErrorMaxInput.set(0)          ##################################CHANGE LATER
		self.simLengthInput.set(5000000.0)           ##################################CHANGE LATER

		self.grid_columnconfigure(0, weight=2)
		self.grid_columnconfigure(1, weight=2)
		self.grid_columnconfigure(2, weight=1)
		self.grid_columnconfigure(3, weight=1)
		self.grid_columnconfigure(4, weight=1)
		self.grid_columnconfigure(5, weight=2)
		self.grid_columnconfigure(6, weight=2)
		self.grid_rowconfigure(0, weight=1)

		# Labels
		labels = ['Number of Servers', 'System Load', 'Interarrival Rate (' + u'\u03bb' + ')', 'Processing Rate (' + u'\u03bc' + ')', '% Error', 'Number of Classes', 'Simulation Length']
		r=0
		c=0
		for elem in labels:
			Label(self, text=elem).grid(row=r, column=c)
			r=r+1
		
		Label(self, textvariable=self.errorMessage, fg="red", font=14).grid(row=7, columnspan=4) #error message, invalid input
		#Label(self, text=u"\u00B1").grid(row=3, column=1) # +/-
		Label(self, text="Min").grid(row=4, column=1, sticky = E) 
		Label(self, text="Max").grid(row=4, column=3, sticky = W) 

		# Entry Boxes
		self.numServersEntry	= Entry(self, textvariable = self.numServersInput)
		self.loadEntry 			= Entry(self, textvariable = self.loadInput)
		self.arrivalRateEntry 	= Entry(self, textvariable = self.arrivalRateInput)
		self.procRateEntry 		= Entry(self, textvariable = self.processingRateInput)
		self.minErrorEntry		= Entry(self, textvariable = self.percentErrorMinInput, width = 5)
		self.maxErrorEntry 		= Entry(self, textvariable = self.percentErrorMaxInput, width = 5)
		self.simLengthEntry 	= Entry(self, textvariable = self.simLengthInput)
		self.numServersEntry.grid(row = 0, column = 1, columnspan = 4)
		self.loadEntry.grid(row = 1, column = 1, columnspan = 4)	
		self.arrivalRateEntry.grid(row = 2, column = 1, columnspan = 4)
		self.procRateEntry.grid(row = 3, column = 1, columnspan = 4)
		self.minErrorEntry.grid(row = 4, column = 2, sticky = E)
		self.maxErrorEntry.grid(row = 4, column = 4, sticky = W)
		self.simLengthEntry.grid(row = 6, column = 1, columnspan = 4)
		self.loadInput.trace('w', self.entryBoxChange)
		self.arrivalRateInput.trace('w', self.entryBoxChange)
		self.refreshLoad()

		# Distribution Dropdowns
		self.distributions = ('Select Distribution', 'Poisson', 'Exponential', 'Uniform', 'Bounded Pareto', 'Custom')
		self.ArrivalDistComboBox = ttk.Combobox(self, values = self.distributions, state = 'disabled')
		self.ArrivalDistComboBox.current(2) # set selection
		self.ArrivalDistComboBox.grid(row = 2, column = 5)
		self.ProcessDistComboBox = ttk.Combobox(self, textvariable = self.comboboxVal, values = self.distributions, state = 'readonly')
		self.ProcessDistComboBox.current(4) # set default selection                  #####################CHANGE LATER
		self.ProcessDistComboBox.grid(row = 3, column = 5)

		self.comboboxVal.trace("w", self.selectionChange) # refresh on change
		self.refreshComboboxes()		

		# Simulate Button
		self.simulateButton = Button(self, text = "SIMULATE", command = self.onButtonClick)
		self.simulateButton.grid(row = 8, columnspan = 6)

	def entryBoxChange(self, name, index, mode):
		self.refreshLoad()

	def refreshLoad(self):
		if len(self.loadEntry.get()) > 0:
			self.arrivalRateEntry.delete(0, 'end')
			self.arrivalRateEntry.configure(state = 'disabled')
		else:
			self.arrivalRateEntry.configure(state = 'normal')

		if len(self.arrivalRateEntry.get()) > 0:
			self.loadEntry.delete(0, 'end')
			self.loadEntry.configure(state = 'disabled')
		else:
			self.loadEntry.configure(state = 'normal')

	def selectionChange(self, name, index, mode):
		self.refreshComboboxes()

	def refreshComboboxes(self):
		selection = self.ProcessDistComboBox.get()
		if selection == 'Bounded Pareto':
			self.procRateEntry.configure(state = 'disabled')
		else:
			self.procRateEntry.configure(state = 'normal')		

	def onButtonClick(self):
		if (self.getNumericValues() == 0) and (self.getDropDownValues() == 0):
				# Send to submit button in main 
				self.simulateButton.event_generate("<<input_simulate>>")

	def getNumericValues(self):
		try:
				numberOfServers = self.numServersInput.get()
				load = self.loadInput.get()
				#arrivalRate = self.arrivalRateInput.get()
				processingRate = self.processingRateInput.get()
				percentErrorMin = self.percentErrorMinInput.get()
				percentErrorMax = self.percentErrorMaxInput.get()
				maxSimLength = self.simLengthInput.get()
		except ValueError:
				self.errorMessage.set("One of your inputs is an incorrect type, try again.")
				return 1
		if load <= 0.0:
				self.errorMessage.set("Load must be non-zero value!")
				return 1
		#if arrivalRate <= 0.0:
		#		self.errorMessage.set("Arrival rate must be non-zero value!")
		#		return 1
		if processingRate <= 0.0:
				self.errorMessage.set("Processing rate must be non-zero value!")
				return 1		
		if maxSimLength <= 0.0:
				self.errorMessage.set("Simulation length must be non-zero value!")
				return 1
		else:
				self.errorMessage.set("")
				Input.valuesList = [numberOfServers, load, processingRate, percentErrorMin, percentErrorMax, maxSimLength]
				return 0

	def getDropDownValues(self):
		comboBox1Value = self.ArrivalDistComboBox.get()
		comboBox2Value = self.ProcessDistComboBox.get()
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

		# Stop Button
		self.stopButton = Button(buttonFrame, text = "STOP SIMULATION", command = self.onStopButtonClick)
		self.stopButton.grid(row = 2, column = 2)		

	def onClearButtonClick(self):
		# Clear console
		self.clearButton.event_generate("<<output_clear>>")

	def onSaveButtonClick(self):
		# Save data
		self.saveButton.event_generate("<<output_save>>")

	def onStopButtonClick(self):
		# Stop simulation
		self.stopButton.event_generate("<<stop_sim>>")

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
	#Size = 0
	NumJobArrayByClass = []
	#Count = 0

	def __init__(self, head = None):
		self.head = head
		LinkedList.NumJobArrayByClass[:] = []
		LinkedList.Count = 0
		self.Size = 0	

	# Insert job into queue (sorted by ERPT)
	def insertByERPT(self, job):
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

		self.Size += 1		

	# Remove first item in queue
	def removeHead(self):
		if (self.Size > 0):
			self.head = self.head.nextNode		# move head forward one node


			self.Size -= 1
			#print "REMOVING HEAD"
		else:
			print "ERROR: The linked list is already empty!"

	# Return first item in queue
	def getHead(self):
		if(self.Size > 0):
			return self.head

	def clear(self):
		self.Size = 0
		self.head = None

	def printList(self, serverID):
		current = self.head
		print "\nJOBS IN QUEUE %s: "%serverID
		while (current != None):
			print "%s, ERPT = %.4f"%(current.job.name, current.job.ERPT)
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
		self.completionTime = 0
		self.procTime = 0
		self.RPT = 0		# Real Remaining Processing Time
		self.ERPT = 0		# Estimated Remaining Processing Time
		self.percentError = 0
		self.processRate = 0
		self.arrivalRate = 0

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
			self.popup=CustomDist(self.master)
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
	def generateError(self, percErrorMin, percErrorMax):
		self.percentError = random.uniform(percErrorMin, percErrorMax)
		return self.percentError

	# Sets all processing times for job
	def setJobAttributes(self, load, procRate, procDist, percErrorMin, percErrorMax):
		if(procDist == 'Bounded Pareto'):
			self.procTime = self.setServiceDist(procRate, procDist) 		#use updated proc rate
			self.setArrProcRates(load, procRate, procDist)
		else:
			self.setArrProcRates(load, procRate, procDist)
			self.procTime = self.setServiceDist(procRate, procDist) 		#use updated proc rate
		self.estimatedProcTime = (1 + (self.generateError(percErrorMin, percErrorMax)/100.0))*self.procTime
		self.RPT = self.procTime
		self.ERPT = self.estimatedProcTime

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
	PreviousJobs = []
	LastClassPrevJobs = []
	CurrentTime = 0.0
	TimeUntilArrival = 0.0
	StopSim = False	

	#print NUM_SERVERS
	#ServerQueues = [LinkedList() for i in range(NUM_SERVERS)] # List of queue for each server
	#ServiceStartTimes = [None] * NUM_SERVERS	# Start times of job in each server
	#ProcessingJobs = [None] * NUM_SERVERS		# Array of current job in each server
	#ServersBusy = [False] * NUM_SERVERS			# Array of whether each server is busy	

	NextRoutedTo = []

	PrevTime = 0
	PrevTimeA = 0
	PrevNumJobs = 0
	AvgNumJobs = 0
	PrevNumJobsArray = []
	NumJobsClass = []
	counter = 0


	def __init__(self, master):
		self.master = master
		#MachineClass.Queue.clear()
		MachineClass.PreviousJobs[:] = []
		MachineClass.LastClassPrevJobs[:] = []
		MachineClass.CurrentTime = 0.0
		MachineClass.TimeUntilArrival = 0.0		
		#MachineClass.ServiceFinishTime = 0
		#MachineClass.ServerBusy = False
		MachineClass.StopSim = False

		#for serverID in range(len(MachineClass.ServerQueues)):
		#	MachineClass.ServerQueues[serverID].clear()
		#MachineClass.ServerQueues = [LinkedList()] * NUM_SERVERS

		#MachineClass.ServerQueues = [MachineClass.Queue1, MachineClass.Queue2] 	# List of queue for each server

		MachineClass.ServiceStartTimes = [None] * NUM_SERVERS
		MachineClass.ProcessingJobs = [None] * NUM_SERVERS
		MachineClass.ServersBusy = [False] * NUM_SERVERS
		MachineClass.WorkLeft = [0.0] * NUM_SERVERS

		MachineClass.NextRoutedTo[:] = []


		MachineClass.PrevTime = 0
		MachineClass.PrevTimeA = 0
		MachineClass.PrevNumJobs = 0
		MachineClass.AvgNumJobs = 0		
		MachineClass.PrevNumJobsArray[:] = []
		MachineClass.NumJobsClass[:] = []
		MachineClass.counter = 0

		NumJobs[:] = []
		NumJobsTime[:] = []
	
		self.ctr = 0

		MachineClass.ServerQueues = [LinkedList() for i in range(NUM_SERVERS)] # List of queue for each server

	# Dictionary of arrival distributions
	def setArrivalDist(self, arrRate, arrDist):
		ArrivalDistributions = {
			'Poisson': random.expovariate(1.0/arrRate),
			'Exponential': random.expovariate(arrRate)
			#'Normal': Rnd.normalvariate(self.inputInstance.valuesList[0])
			#'Custom':
		}
		return ArrivalDistributions[arrDist]
	
	#def getFirstQueued(self):
	#	job = None
	#	if (MachineClass.Queue.head != None):
	#		job = MachineClass.Queue.head.job
	#	return job

	#def removeFirstQueued(self):
	#	MachineClass.Queue.removeHead()	# remove first job from queue

	#update data
	def updateJobs(self):
		for serverID in range(NUM_SERVERS):
			if(MachineClass.ProcessingJobs[serverID] != None):
				serviceTime = MachineClass.CurrentTime - MachineClass.ServiceStartTimes[serverID]
				MachineClass.ProcessingJobs[serverID].RPT -= serviceTime
				MachineClass.ProcessingJobs[serverID].ERPT -= serviceTime
				MachineClass.WorkLeft[serverID] -= serviceTime
				MachineClass.ServiceStartTimes[serverID] = MachineClass.CurrentTime


	# Router sends job to servers and adds job to their queue
	# Compare to server last routed to of the same class, send to next one
	def router(self, job):
		# Get serverID where there is min work left
		serverID = MachineClass.WorkLeft.index(min(MachineClass.WorkLeft))
				
		#if(self.ctr == 0):
		#	self.sendJobToServer(job, 0)					#First job is always Class 0, so update for next arrival								
		#	# Return server id job is routed to
		#	return 0

		#else:
		self.sendJobToServer(job, serverID)
		
		# Return server id job is routed to
		return serverID
					
					


	# Send job to server i
	def sendJobToServer(self, job, serverID):
	##	Insert by ERPT
		# Add current job with new class to queue 
		MachineClass.ServerQueues[serverID].insertByERPT(job)				# add job to queue
		MachineClass.WorkLeft[serverID] += job.ERPT
		#GUI.writeToConsole(self.master, "sending job %s, ERPT %s to server %s"%(job.name, job.ERPT, serverID))

	def calcNumJobs(self, jobID):
		self.currentNumJobs = 0
		for serverID in range(NUM_SERVERS):
			# Firstly, add all jobs that are waiting in queue
			self.currentNumJobs += MachineClass.ServerQueues[serverID].Size

			# Secondly, add jobs that are currently processing to the total number in the system
			if(MachineClass.ServersBusy[serverID] == True):
				self.currentNumJobs += 1
		
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

		NumJobs.append(MachineClass.AvgNumJobs)				# y axis of plot
		NumJobsTime.append(MachineClass.CurrentTime)		# x axis of plot


	# Job arriving
	def arrivalEvent(self, load, arrDist, procRate, procDist, percErrorMin, percErrorMax):
		J = JobClass(self.master)
		J.setJobAttributes(load, procRate, procDist, percErrorMin, percErrorMax)
		J.name = "Job%02d"%self.ctr
		
		self.calcNumJobs(self.ctr)

		self.updateJobs()		# update all processing jobs

		#add processing job back to the queue by ERPT and it will decide if it is worht 

		serverID = self.router(J)									# Send job to a server queue
		procJob = MachineClass.ProcessingJobs[serverID]

		GUI.writeToConsole(self.master, "%.6f | %s arrived, erpt = %s, server = %s"%(MachineClass.CurrentTime, J.name, J.ERPT, serverID))		
		GUI.writeToConsole(self.master, "---------- | Work left array %s"%(MachineClass.WorkLeft))		

		# Preempt processing job at server if new job has higher priority class
		if (procJob != None):
			if (J.ERPT < procJob.ERPT):
				GUI.writeToConsole(self.master, "---------- | %s preempting %s"%(J.name, procJob.name))

				#Remove procJob from processing
				MachineClass.ServersBusy[serverID] = False
				MachineClass.ProcessingJobs[serverID] = None
				MachineClass.ServiceStartTimes[serverID] = None

				# Add preempted job back to queue
				MachineClass.ServerQueues[serverID].insertByERPT(procJob);
				GUI.writeToConsole(self.master, "---------- | %s added back to server %s by ERPT=%s"%(procJob.name, serverID, procJob.ERPT))

				
		
		self.processJobs()		# process first job in each queue

		MachineClass.TimeUntilArrival = self.setArrivalDist(J.arrivalRate, arrDist)
		self.ctr += 1

	# Processing first job in queue
	def processJobs(self):
		for serverID in range(NUM_SERVERS):
			#Server i not busy and a job is waiting in the queue
			if (MachineClass.ServersBusy[serverID] == False) and (MachineClass.ServerQueues[serverID].Size > 0):
				currentJob = MachineClass.ServerQueues[serverID].getHead().job

				MachineClass.ServiceStartTimes[serverID] = MachineClass.CurrentTime
				MachineClass.ProcessingJobs[serverID] = currentJob
				MachineClass.ServersBusy[serverID] = True
				GUI.writeToConsole(self.master, "---------- | %s processing on server %s"%(currentJob.name, serverID))
				MachineClass.ServerQueues[serverID].removeHead()

	# Job completed
	def completionEvent(self, completingJob, load, percErrorMin, percErrorMax):
		completingJob.completionTime = MachineClass.CurrentTime

		self.calcNumJobs(self.ctr)

		# Server no longer busy
		serverID = MachineClass.ProcessingJobs.index(completingJob)
		MachineClass.ServersBusy[serverID] = False
		MachineClass.ProcessingJobs[serverID] = None
		MachineClass.ServiceStartTimes[serverID] = None

		GUI.writeToConsole(self.master, "%.6f | %s COMPLTED at server %s"%(MachineClass.CurrentTime, completingJob.name, serverID))

		#Update other processing jobs (in case next event should be completion)
		self.updateJobs()

		#Once job has completed remove any remaining processing time for that job due to error estimation
		MachineClass.WorkLeft[serverID] -= completingJob.ERPT

		#If there is a job waiting for this server, process it
		if (MachineClass.ServerQueues[serverID].Size > 0):
			self.processJobs()
		else:
			MachineClass.WorkLeft[serverID] = 0.0 ################### TO COMPENSATE FOR FLOATING POINT ERROR
																 #### some variables hold more sig digs than others... why?


	def run(self, load, arrDist, procRate, procDist, percErrorMin, percErrorMax, simLength):
		while 1:
			# Generate time of first job arrival
			if(self.ctr == 0):
				arrRate = float(load) / procRate
				MachineClass.TimeUntilArrival = self.setArrivalDist(arrRate, arrDist) # generate next arrival


			# Find shortest RPT of all processing jobs		
			try:
				minRPT = min(element.RPT for element in MachineClass.ProcessingJobs if element is not None) # gets min rpt value
				l = [x for x in MachineClass.ProcessingJobs if (x is not None and x.RPT == minRPT)]			# searches for job wiht min rpt value
				minProcJob = l[0]
				#GUI.writeToConsole(self.master, "%.4F || Min proc job %s, RPT=%s, ERPT=%s"%(MachineClass.CurrentTime, minProcJob.name, minProcJob.RPT, minProcJob.ERPT))
			except ValueError:
				minRPT = -1	
				minProcJob = None				

			# If all servers are idle, or next arrival is before completion of shortest job processing next event is ARRIVAL
			if (all(element == False for element in MachineClass.ServersBusy)) or (MachineClass.TimeUntilArrival < minRPT):
				MachineClass.CurrentTime += MachineClass.TimeUntilArrival
				self.arrivalEvent(load, arrDist, procRate, procDist, percErrorMin, percErrorMax)

			#next event is job finishing (job with shortest RPT)			
			else:
				completingJob = minProcJob
				MachineClass.CurrentTime += completingJob.RPT
				self.completionEvent(completingJob, load, percErrorMin, percErrorMax)

			# If current time is greater than the simulation length, end program
			if (MachineClass.CurrentTime > simLength) or (MachineClass.StopSim == True):
				break



#----------------------------------------------------------------------#
def main():
	window = GUI(None)                           			   # instantiate the class with no parent (None)
	window.title('SRPT Multi Least Work Left')  # title the window

	# Global variables used in JobClass
	main.timesClicked = 0       
	main.customEquation = ""

	#window.geometry("500x600")                     # set window size
	window.mainloop()                               # loop indefinitely, wait for events


if __name__ == '__main__': main()
