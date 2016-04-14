#----------------------------------------------------------------------#
# SRPTE.py
#
# This application simulates multiple servers with Poisson arrivals
# and processing times of a general distribution. There are errors in
# time estimates within a range. Jobs are serviced in order of shortest 
# remaining processing time.
#
# Rachel Mailach
#----------------------------------------------------------------------#

from Tkinter import *
from datetime import datetime
#import plotly.plotly as py
#from plotly.graph_objs import Scatter
#import plotly.graph_objs as go
import random
import tkMessageBox
import ttk
import tkFileDialog
import sqlite3
import pandas

conn=sqlite3.connect('MultiServerDatabase.db')

NumJobs = []
NumJobsTime = []
TimeSys = []
ProcTime = []
PercError = []
NUM_SERVERS = 0

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
		SEED = datetime.now() 
		random.seed(SEED)

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

	# Empty old saves at the begining of each simulation
	def clearSavedJobs(self):
		with open("Jobs.xls", "w") as myFile:
			myFile.write('Job Name,Completion Time' + '\n')
			myFile.close()

	def clearSavedArrivals(self):
		with open("Arrivals.xls", "w") as myFile:
			myFile.write('Job Name,Arrival Time,RPT,ERPT' + '\n')
			myFile.close()

	def clearSavedNumJobs(self):
		with open("AvgNumberOfJobs.xls", "w") as myFile:
			myFile.write('Current Time, Average Number Of Jobs, Current Number Of Jobs' + '\n')
			myFile.close()

	def clearConsole(self, event):
		self.console.config(state=NORMAL)       # make console editable
		self.console.delete('1.0', END)
		self.console.config(state=DISABLED)     # disable (non-editable) console

	def updateStatusBar(self, text=' '):
		self.statusText.set(text)
	
	def printIntro(self):
		self.writeToConsole("SRPTE \n\n This application simulates a single server with Poisson arrivals and processing times of a general distribution. Each arrival has an estimation error within a percent error taken as input. Jobs are serviced in order of shortest remaining processing time.")

	def saveParams(self, numServers, load, arrRate, arrDist, procRate, procDist, percErrorMin, percErrorMax, simLength, alpha, lower, upper):
		##params = pandas.DataFrame(columns=('seed', 'numServers', 'load', 'arrRate', 'arrDist', 'procRate', 'procDist', 'alpha', 'lower', 'upper', 'percErrorMin', 'percErrorMax', 'simLength'))
		print SEED
		params = pandas.DataFrame({	'seed' : [SEED],
									'numServers' : [numServers],
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
									'avgNumJobs' : [MachineClass.AvgNumJobs]
									})

		params.to_sql(name='parameters', con=conn, if_exists='append')
		print params

	def printParams(self, numServers, load, arrDist, procRate, procDist, percErrorMin, percErrorMax, simLength):
		self.writeToConsole("--------------------------------------------------------------------------------")
		self.writeToConsole("PARAMETERS:")
		self.writeToConsole("Number of Servers = %s"%numServers)
		self.writeToConsole("Load = %.4f"%load)
		#self.writeToConsole("Arrival Rate = %.4f"%arrRate)
		self.writeToConsole("Arrival Distribution = %s"%arrDist)
		self.writeToConsole("Processing Rate = %.4f, Processing Distribution = %s"%(procRate, str(procDist)))
		self.writeToConsole("% Error  = " + u"\u00B1" + " %.4f, %.4f"%(percErrorMin, percErrorMax))
		self.writeToConsole("Simulation Length = %.4f\n\n"%simLength)

	def calcVariance(self, List, avg):
		var = 0
		for i in List:
			var += (avg - i)**2
		return var/len(List)

	def displayAverageData(self):
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
		#self.writeToConsole('Service order: %s\n\n' % MachineClass.JobOrderOut)

	# def plotNumJobsInSys(self, load, errorMin, errorMax):
	# 	py.sign_in('mailacrs','wowbsbc0qo')


	# 	if (abs(errorMin) == errorMax):
	# 		self.error = str(int(errorMax))
	# 	else:
	# 		self.error = str(int(errorMin)) + "_" + str(int(errorMax))

	# 	self.name = "NumJobs_numServers=%s_load=%s_alpha=%s_error=%s"%(NUM_SERVERS, load, JobClass.BPArray[0], self.error)
	# 	params = pandas.read_csv(self.name)

	# 	trace0 = Scatter(x=params["NumJobsTime"], y=params["NumJobs"])
	# 	data = [trace0]
	# 	layout = go.Layout(
	# 		title='Average Number of Jobs Over Time',
	# 		xaxis=dict(
	# 			title='Time',
	# 			titlefont=dict(
	# 			family='Courier New, monospace',
	# 			size=18,
	# 			color='#7f7f7f'
	# 		)
	# 	),
	# 		yaxis=dict(
	# 			title='Number of Jobs',
	# 			titlefont=dict(
	# 			family='Courier New, monospace',
	# 			size=18,
	# 			color='#7f7f7f'
	# 		)
	# 	)
	# 	)
	# 	fig = go.Figure(data=data, layout=layout)
	# 	unique_url = py.plot(fig, filename = 'SRPT_NumJobsInSys: '+ str(self.name))


	def stopSimulation(self, event):
		MachineClass.StopSim = True

	def submit(self, event):
		self.updateStatusBar("Simulating...")
		#self.clearSavedJobs()
		#self.clearSavedArrivals()
		#self.clearSavedNumJobs()
		I = Input(self)

		# Set global variable for num servers to value inputed
		global NUM_SERVERS
		NUM_SERVERS = I.valuesList[0]

		self.printParams(I.valuesList[0],					#num Servers
						 I.valuesList[1],					#load
						 #I.valuesList[2],					# arrival rate
						 'Exponential',						#arrival
						 I.valuesList[3], I.distList[1],	#processing rate
						 I.valuesList[4], 					#error min
						 I.valuesList[5],					#error max 
						 I.valuesList[6])					#sim time

		main.timesClicked = 0
		
		# Start process
		MC = MachineClass(self)
		MC.run(	#I.valuesList[0],					#num Servers
				I.valuesList[1],					#load
				#I.valuesList[2],					# arrival rate
				'Exponential',						# arrival
				I.valuesList[3], I.distList[1],		# processing
				I.valuesList[4], 					# error min
				I.valuesList[5],					# error max
				I.valuesList[6])					# sim time

		self.saveParams(I.valuesList[0],				#num Servers
						I.valuesList[1],				#load
						I.valuesList[2],							# arrival rate
						'Exponential',					# arrival dist
						I.valuesList[3], I.distList[1],	# processing
						I.valuesList[4], 				# error min
						I.valuesList[5],				# error max
						I.valuesList[6],				# sim time
						JobClass.BPArray[0],			# alpha
						JobClass.BPArray[1],			# lower
						JobClass.BPArray[2])			# upper





		self.displayAverageData()
		#self.plotNumJobsInSys(I.valuesList[1], I.valuesList[4], I.valuesList[5])
		#self.saveData()
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

		self.numServersInput.set(2)				##################################CHANGE LATER	
		self.loadDefault = 0.8					##################################CHANGE LATER	
		self.arrRateDefault = 0.8				##################################CHANGE LATER
		self.procRateDefault = 0.5				##################################CHANGE LATER

		self.loadInput.set(self.loadDefault)
		#self.arrivalRateInput.set(self.arrRateDefault)
		self.processingRateInput.set(self.procRateDefault)
		self.percentErrorMinInput.set(-20)
		self.percentErrorMaxInput.set(20)
		self.simLengthInput.set(100.0)

		self.grid_columnconfigure(0, weight=2)
		self.grid_columnconfigure(1, weight=2)
		self.grid_columnconfigure(2, weight=1)
		self.grid_columnconfigure(3, weight=1)
		self.grid_columnconfigure(4, weight=1)
		self.grid_columnconfigure(5, weight=2)
		self.grid_rowconfigure(0, weight=1)

		# Labels
		labels = ['Number of Servers', 'System Load', 'Interarrival Rate (' + u'\u03bb' + ')', 'Processing Rate (' + u'\u03bc' + ')', '% Error' , 'Simulation Length']
		r=0
		c=0
		for elem in labels:
			Label(self, text=elem).grid(row=r, column=c)
			r=r+1
		
		Label(self, textvariable=self.errorMessage, fg="red", font=14).grid(row=6, columnspan=4) #error message, invalid input
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
		self.simLengthEntry.grid(row = 5, column = 1, columnspan = 4)		
		self.loadInput.trace('w', self.entryBoxChange)
		self.arrivalRateInput.trace('w', self.entryBoxChange)
		self.refreshLoad()		

		# Distribution Dropdowns
		self.distributions = ('Select Distribution', 'Poisson', 'Exponential', 'Uniform', 'Bounded Pareto', 'Custom')
		self.ArrivalDistComboBox = ttk.Combobox(self, values = self.distributions, state = 'disabled')
		self.ArrivalDistComboBox.current(2) # set selection
		self.ArrivalDistComboBox.grid(row = 1, column = 5)
		self.ProcessDistComboBox = ttk.Combobox(self, textvariable = self.comboboxVal, values = self.distributions, state = 'readonly')
		self.ProcessDistComboBox.current(4) # set default selection                  #####################CHANGE LATER
		self.ProcessDistComboBox.grid(row = 2, column = 5)

		self.comboboxVal.trace("w", self.selectionChange) # refresh on change
		self.refreshComboboxes()

		# Simulate Button
		self.simulateButton = Button(self, text = "SIMULATE", command = self.onButtonClick)
		self.simulateButton.grid(row = 7, columnspan = 6)

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
			#self.procRateEntry.delete(0, 'end')
			self.procRateEntry.configure(state = 'disabled')
		else:
			self.procRateEntry.configure(state = 'normal')
			#self.processingRateInput.set(self.procRateDefault)

	def onButtonClick(self):
		if (self.getNumericValues() == 0) and (self.getDropDownValues() == 0):
				# Send to submit button in main 
				self.simulateButton.event_generate("<<input_simulate>>")

	def getNumericValues(self):
		try:
			numberOfServers = self.numServersInput.get()
			load = self.loadInput.get()
			percentErrorMin = self.percentErrorMinInput.get()
			percentErrorMax = self.percentErrorMaxInput.get()
			maxSimLength = self.simLengthInput.get()
		except ValueError:
			self.errorMessage.set("One of your inputs is an incorrect type, try again.")
			return 1

		try:
			arrRate = float(self.arrivalRateInput.get())
		except ValueError:
			arrRate = 0.0
		try:
			procRate = float(self.processingRateInput.get())
		except ValueError:
			procRate = 0.0

		if load <= 0.0:
			self.errorMessage.set("System load must be a non-zero value!")
			return 1
		#if arrRate <= 0.0:
		#	self.errorMessage.set("Arrival rate must be a non-zero value!")
		#	return 1
		#if procRate != None and processingRate <= 0.0:
		#	self.errorMessage.set("Processing rate must be a non-zero value!")
		#	return 1



		if maxSimLength <= 0.0:
			self.errorMessage.set("Simulation length must be a non-zero value!")
			return 1
		else:
			self.errorMessage.set("")
			Input.valuesList = [numberOfServers, load, arrRate, procRate, percentErrorMin, percentErrorMax, maxSimLength]
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
			print "ERROR: The linked list is already empty!!"

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
		self.completionTime = 0
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
	def generateError(self, percErrorMin, percErrorMax):
		self.percentError = random.randint(percErrorMin, percErrorMax)
		return self.percentError

	# Sets all processing times for job
	def setJobAttributes(self, load, procRate, procDist, percErrorMin, percErrorMax, jobArrival):
		if(procDist == 'Bounded Pareto'):
			self.procTime = self.setServiceDist(procRate, procDist) 		#use updated proc rate
			self.setArrProcRates(load, procRate, procDist)
		else:
			self.setArrProcRates(load, procRate, procDist)
			self.procTime = self.setServiceDist(procRate, procDist) 		#use updated proc rate
		self.estimatedProcTime = (1 + (self.generateError(percErrorMin, percErrorMax)/100.0))*self.procTime
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
	
	AvgNumJobs = 0
	PrevTime = 0
	PrevNumJobs = 0

	StopSim = False
	ServiceStartTimes = [None] * NUM_SERVERS	# Start times of job in each server
	ProcessingJobs = [None] * NUM_SERVERS		# Array of current job in each server
	ServersBusy = [False] * NUM_SERVERS			# Array of whether each server is busy

	def __init__(self, master):
		self.master = master
		MachineClass.Queue.clear()
		LinkedList.Size = 0
		MachineClass.CurrentTime = 0.0
		MachineClass.TimeUntilArrival = 0.0
		MachineClass.StopSim = False	

		MachineClass.ServiceStartTimes = [None] * NUM_SERVERS
		MachineClass.ProcessingJobs = [None] * NUM_SERVERS
		MachineClass.ServersBusy = [False] * NUM_SERVERS			
		
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
	
	def getFirstQueued(self):
		job = None
		if (MachineClass.Queue.head != None):
			job = MachineClass.Queue.head.job
		return job

	def removeFirstQueued(self):
		MachineClass.Queue.removeHead()	# remove first job from queue

	#update data
	def updateJobs(self):
		for index in range(NUM_SERVERS):
			if(MachineClass.ProcessingJobs[index] != None):
				serviceTime = MachineClass.CurrentTime - MachineClass.ServiceStartTimes[index]
				MachineClass.ProcessingJobs[index].RPT -= serviceTime
				MachineClass.ProcessingJobs[index].ERPT -= serviceTime

	def calcNumJobs(self, jobID):
		self.currentNumJobs = 0

		# First add all jobs that are currently being processed
		for i in range(NUM_SERVERS):
			if(MachineClass.ServersBusy[i] == True):
				self.currentNumJobs += 1

		# Secondly, add all jobs in queue
		self.currentNumJobs += MachineClass.Queue.Size
		

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

	def saveNumJobs(self, currentTime, avgNumJobs, load, errorMin, errorMax):
		text = "%.6f,%.6f"%(currentTime, avgNumJobs) + "\n"

		if (abs(errorMin) == errorMax):
			self.error = str(int(errorMax))
		else:
			self.error = str(int(errorMin)) + "_" + str(int(errorMax))
		
		with open("NumJobs_numServers=%s_load=%s_alpha=%s_error=%s.xls"%(NUM_SERVERS, load, JobClass.BPArray[0], self.error), "a") as myFile:
			myFile.write(text)
		myFile.close()		

	#def saveArrivals(self, job, load, errorMin, errorMax):
	#	text = "%s,%.6f,%.6f,%.6f"%(job.name, job.arrivalTime, job.RPT, job.ERPT) + "\n"
	#
	#	if (abs(errorMin) == errorMax):
	#		self.error = str(int(errorMax))
	#	else:
	#		self.error = str(int(errorMin)) + "_" + str(int(errorMax))	
	#	
	#	with open("Arrivals_numServers=%s_load=%s_alpha=%s_error=%s.xls"%(NUM_SERVERS, load, JobClass.BPArray[0], self.error), "a") as myFile:
	#		myFile.write(text)
	#	myFile.close()		

	#def saveJobs(self, job, load, errorMin, errorMax):
	#	text = "%s,%.6f"%(job.name, job.completionTime) + "\n"
	#
	#	if (abs(errorMin) == errorMax):
	#		self.error = str(int(errorMax))
	#	else:
	#		self.error = str(int(errorMin)) + "_" + str(int(errorMax))

	#	with open("Jobs_numServers=%s_load=%s_alpha=%s_error=%s.xls"%(NUM_SERVERS, load, JobClass.BPArray[0], self.error), "a") as myFile:
	#		myFile.write(text)
	#	myFile.close()				

	# Job arriving
	def arrivalEvent(self, load, arrDist, procRate, procDist, percErrorMin, percErrorMax):
		J = JobClass(self.master)
		J.setJobAttributes(load, procRate, procDist, percErrorMin, percErrorMax, MachineClass.CurrentTime)
		J.name = "Job%02d"%self.ctr

		GUI.writeToConsole(self.master, "%.6f | %s arrived, ERPT = %.5f"%(MachineClass.CurrentTime, J.name, J.ERPT))	
		self.updateJobs()				# update all processing jobs
	

		# Find longest RPT of all processing jobs
		try:				
			maxERPT = max(element.ERPT for element in MachineClass.ProcessingJobs if element is not None)
			l = [x for x in MachineClass.ProcessingJobs if (x is not None and x.ERPT == maxERPT)]
			maxProcJob = l[0]

			# Preempt largest job processing if all servers busy
			if (maxERPT > J.ERPT)and(all(element == True for element in MachineClass.ServersBusy)):
				GUI.writeToConsole(self.master, "%.6f | %s preempting %s"%(MachineClass.CurrentTime, J.name, maxProcJob.name))
				#Remove maxProcJob from server
				serverIndex = MachineClass.ProcessingJobs.index(maxProcJob)
				MachineClass.ServersBusy[serverIndex] = False
				MachineClass.ProcessingJobs[serverIndex] = None
				MachineClass.ServiceStartTimes[serverIndex] = None

				#add back to queue
				MachineClass.Queue.insert(maxProcJob)	# add job to queue
				GUI.writeToConsole(self.master, "%.6f | %s added back to queue, ERPT = %.5f"%(MachineClass.CurrentTime, maxProcJob.name, maxProcJob.ERPT))

		except ValueError:
			maxERPT = 10^100
			maxProcJob = None			

		MachineClass.Queue.insert(J)	# add job to queue
		#self.calcNumJobs(self.ctr)
		#self.saveNumJobs(MachineClass.CurrentTime, MachineClass.AvgNumJobs, load, percErrorMin, percErrorMax)
		#self.saveArrivals(J, load, percErrorMin, percErrorMax)
		self.processJobs()				# process first job in queue	

		# Generate next arrival
		MachineClass.TimeUntilArrival = self.setArrivalDist(J.arrivalRate, arrDist)
		self.ctr += 1

	# Processing first job in queue
	def processJobs(self):
		for index in range(NUM_SERVERS):
			currentJob = self.getFirstQueued()

			#Server not busy and a job is waiting is in the queue
			if (MachineClass.ServersBusy[index] == False) and (currentJob != None): 	
				MachineClass.ServiceStartTimes[index] = MachineClass.CurrentTime
				MachineClass.ProcessingJobs[index] = currentJob
				MachineClass.ServersBusy[index] = True
				GUI.writeToConsole(self.master, "%.6f | %s processing on server %s"%(MachineClass.CurrentTime, currentJob.name, index))
				self.removeFirstQueued()

	# Job completed
	def completionEvent(self, completingJob, load, percErrorMin, percErrorMax):
		completingJob.completionTime = MachineClass.CurrentTime
		#self.saveJobs(completingJob, load, percErrorMin, percErrorMax)			# save to list of arrivals, for testing

		# Server no longer busy
		serverIndex = MachineClass.ProcessingJobs.index(completingJob)
		MachineClass.ServersBusy[serverIndex] = False
		MachineClass.ProcessingJobs[serverIndex] = None
		MachineClass.ServiceStartTimes[serverIndex] = None

		#MachineClass.JobOrderOut.append(completingJob.name)
		self.calcNumJobs(self.ctr)
		TimeSys.append(MachineClass.CurrentTime - completingJob.arrivalTime)
		ProcTime.append(completingJob.procTime)
		PercError.append(abs(completingJob.percentError))

		GUI.writeToConsole(self.master, "%.6f | %s COMPLTED"%(MachineClass.CurrentTime, completingJob.name))


	def run(self, load, arrDist, procRate, procDist, percErrorMin, percErrorMax, simLength):
		while 1:
			if(self.ctr == 0):	# set time of first job arrival
				arrRate = float(load) / procRate
				MachineClass.TimeUntilArrival = self.setArrivalDist(arrRate, arrDist) # generate next arrival

			# Find shortest RPT of all processing jobs		
			try:
				minRPT = min(element.RPT for element in MachineClass.ProcessingJobs if element is not None)
				l = [x for x in MachineClass.ProcessingJobs if (x is not None and x.RPT == minRPT)]
				minProcJob = l[0]
			except ValueError:
				minRPT = -1	
				minProcJob = None

			# If all servers are idle, or next arrival is before completion of shortest job processing next event is ARRIVAL
			if (all(element == False for element in MachineClass.ServersBusy)) or (MachineClass.TimeUntilArrival < minRPT):
				MachineClass.CurrentTime += MachineClass.TimeUntilArrival

				# stop server from processing current job
				#MachineClass.ServerBusy == False
				self.arrivalEvent(load, arrDist, procRate, procDist, percErrorMin, percErrorMax)
			
			#next event is job finishing (job with shortest RPT)			
			else:
				completingJob = minProcJob
				MachineClass.CurrentTime += completingJob.RPT
				self.completionEvent(completingJob, load, percErrorMin, percErrorMax)

				if(MachineClass.Queue.Size > 0):
					self.processJobs()

			# If current time is greater than the simulation length, end program
			if (MachineClass.CurrentTime > simLength) or (MachineClass.StopSim == True):
				break


#----------------------------------------------------------------------#
def main():
	window = GUI(None)                              # instantiate the class with no parent (None)
	window.title('Multi-Server SRPT with Errors')  # title the window

	# Global variables used in JobClass
	main.timesClicked = 0       
	main.customEquation = ""

	#window.geometry("500x600")                     # set window size
	window.mainloop()                               # loop indefinitely, wait for events


if __name__ == '__main__': main()
