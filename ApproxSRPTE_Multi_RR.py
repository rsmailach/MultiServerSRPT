#----------------------------------------------------------------------#
# ApproxSRPTE_Multi_RR.py
#
# This application simulates multiple server with Poisson arrivals
# and processing times of a general distribution. There are errors in
# time estimates within a range. Arrivals are assigned to SRPT classes
# using the methods described in Adaptive and Scalable Comparison
# Scheduling. Servers are assigned jobs using Round Robin scheduling.
#
# Rachel Mailach
#----------------------------------------------------------------------#

from Tkinter import *
from datetime import datetime
from math import log
#import plotly.plotly as py
#from plotly.graph_objs import Scatter
#import plotly.graph_objs as go
from bokeh.plotting import figure, output_file, show
from bokeh.charts import Bar, output_file, show
from collections import OrderedDict
import pandas
from itertools import cycle

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
#NUM_SERVERS = 0

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
		self.seed = random.seed(datetime.now())

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

	def printParams(self, numServers, load, arrDist, procRate, procDist, percErrorMin, percErrorMax, numClasses, simLength): 
		self.writeToConsole("--------------------------------------------------------------------------------")
		self.writeToConsole("PARAMETERS:")
		self.writeToConsole("Number of Servers = %s"%numServers)
		self.writeToConsole("Load = %.4f"%load)
		#self.writeToConsole("Arrival Rate = %.4f"%arrRate)
		self.writeToConsole("Arrival Distribution = %s"%arrDist)
		self.writeToConsole("Processing Rate = %.4f, Processing Distribution = %s"%(procRate, str(procDist)))
		self.writeToConsole("% Error  = " + " %.4f, %.4f"%(percErrorMin, percErrorMax))
		self.writeToConsole("Number of Classes = %d"%numClasses)
		self.writeToConsole("Simulation Length = %.4f\n\n"%simLength)

	def plotNumJobsInSys(self, numClasses):
		# SCATTER PLOT
		output_file("SRPT_NumJobsInSys: Case 4")
		scatter = figure(title = "Average Number of Jobs Over Time",
						x_axis_label = "Time",
						y_axis_label = "Number of Jobs")
		#trace0.scatter(NumJobsTime, NumJobs)
		scatter.line(NumJobsTime, NumJobs)
		scatter.circle(NumJobsTime, NumJobs, size=1)
		show(scatter)



		#-----------------------------------------------------------------------------#
		# BLOCK DIAGRAM
		output_file("SRPT_NumJobsInSysPerClass: Case4")

		classRange = range(1, numClasses + 1)
		classes = [format(i,'02d') for i in classRange]

		# remove placeholder element
		MachineClass.AvgNumJobsArray.pop(0)

		dictionary = {'number of jobs': MachineClass.AvgNumJobsArray, 'classes': classes}
		df = pandas.DataFrame(data=dictionary)

		bar = Bar(df, 'classes', values='number of jobs', title="test chart")
		show(bar)

	# def plotNumJobsInSys1(self, numClasses):
	# 	py.sign_in('mailacrs','wowbsbc0qo')
	# 	trace0 = Scatter(x=NumJobsTime, y=NumJobs)
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
	# 	unique_url = py.plot(fig, filename = 'SRPT_NumJobsInSys: Case1')

	# 	#-----------------------------------------------------------------------------#
	# 	# Average jobs/class
	# 	trace1 = go.Bar(y= MachineClass.AvgNumJobsArray)
		
	# 	data1 = [trace1]
	# 	layout1 = go.Layout(
	# 		title='Average Number of Jobs Per Class',
	# 		xaxis=dict(
	# 			title='Classes',
	# 			range=[1,numClasses],              # set range
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
	# 	fig1 = go.Figure(data=data1, layout=layout1)
	# 	unique_url1 = py.plot(fig1, filename = 'SRPT_NumJobsInSysPerClass: Case1')

	def calcVariance(self, List, avg):
		var = 0
		for i in List:
			var += (avg - i)**2
		return var/len(List)

	def displayAverageData(self, numClasses):
		self.plotNumJobsInSys(numClasses)
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
		#self.writeToConsole('Service order: %s\n\n' % MachineClass.JobOrderOut)

	def stopSimulation(self, event):
		MachineClass.StopSim = True
				
	def submit(self, event):
		self.updateStatusBar("Simulating...")
		self.clearSavedArrivals()
		I = Input(self)   

		# Set global variable for num servers to value inputed  
		global NUM_SERVERS
		NUM_SERVERS = I.valuesList[0]

		self.printParams(I.valuesList[0],					#num Servers
						 I.valuesList[1],					#load
						 'Exponential',						#arrival
						 I.valuesList[2], I.distList[1], 	#processing rate
						 I.valuesList[3],					#error min
						 I.valuesList[4],					#error max
						 I.valuesList[5], 					#num Classes
						 I.valuesList[6])					#sim time

		main.timesClicked = 0
		
		# Start process
		MC = MachineClass(self)
		MC.run(	I.valuesList[0],				#num Servers
				I.valuesList[1],				#load
				'Exponential',					#arrival
				I.valuesList[2], I.distList[1],	# proc
				I.valuesList[3],				# error min
				I.valuesList[4],				# error max
				I.valuesList[5],				# num class
				I.valuesList[6])				# sim time

		#self.displayAverageData(I.valuesList[5])
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
		self.numberOfClassesInput = IntVar()
		self.simLengthInput = DoubleVar()
		self.errorMessage = StringVar()
		self.comboboxVal = StringVar()

		self.numServersInput.set(2)					##################################CHANGE LATER	
		self.loadInput.set(0.95)       		 	   	##################################CHANGE LATER
		#self.arrivalRateInput.set(1.0)         	 ##################################CHANGE LATER
		self.processingRateInput.set(0.5)   	    ##################################CHANGE LATER
		self.percentErrorMinInput.set(0)          ##################################CHANGE LATER
		self.percentErrorMaxInput.set(0)          ##################################CHANGE LATER
		self.numberOfClassesInput.set(10)			##################################CHANGE LATER
		self.simLengthInput.set(100.0)           ##################################CHANGE LATER

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
		self.numClassesEntry 	= Entry(self, textvariable = self.numberOfClassesInput)
		self.simLengthEntry 	= Entry(self, textvariable = self.simLengthInput)
		self.numServersEntry.grid(row = 0, column = 1, columnspan = 4)
		self.loadEntry.grid(row = 1, column = 1, columnspan = 4)	
		self.arrivalRateEntry.grid(row = 2, column = 1, columnspan = 4)
		self.procRateEntry.grid(row = 3, column = 1, columnspan = 4)
		self.minErrorEntry.grid(row = 4, column = 2, sticky = E)
		self.maxErrorEntry.grid(row = 4, column = 4, sticky = W)
		self.numClassesEntry.grid(row = 5, column = 1, columnspan = 4)
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
				numberOfClasses = self.numberOfClassesInput.get()
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
		if numberOfClasses < 1.0:
				self.errorMessage.set("There must be at least one class!")
				return 1		
		if maxSimLength <= 0.0:
				self.errorMessage.set("Simulation length must be non-zero value!")
				return 1
		else:
				self.errorMessage.set("")
				Input.valuesList = [numberOfServers, load, processingRate, percentErrorMin, percentErrorMax, numberOfClasses, maxSimLength]
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

	# Insert job into queue (sorted by class, then name)
	def insertByClass(self, job):
		current = self.head		# node iterator, starts at head
		previous = None
		if (current == None):	# if queue is empty, set current job as head
			self.head = Node(job, None)
		else:
			while (current != None) and (job.priorityClass >= current.job.priorityClass):# and (job.name > current.job.name):
				previous = current 				# prev = node[i]
				current = current.nextNode 		# current = node[i+1]
			
			# Insert new node after previous before current
			if (previous == None):
				self.head = Node(job, current)
			else:
				previous.nextNode = Node(job, current)

		self.Size += 1
		#print "ENQUEUE JOB"

	#Insert to queue and sort by ERPT
	def insertByERPT(self, job, numClasses):
		current = self.head		# node iterator, starts at head
		previous = None
		if (current == None):	# if queue is empty, set current job as head
			self.head = Node(job, None)
		else:
			while (current != None) and (job.priorityClass >= current.job.priorityClass) and (job.ERPT > current.job.ERPT):
				previous = current 				# prev = node[i]
				current = current.nextNode 		# current = node[i+1]
			
			# Insert new node after previous before current
			if (previous == None):
				self.head = Node(job, current)
			else:
				previous.nextNode = Node(job, current)

		self.Size += 1
		#print "ENQUEUE JOB"	

	#Insert to queue and sort by LCFS
	def insertByLCFS(self, job, numClasses):
		current = self.head		# node iterator, starts at head
		previous = None
		if (current == None):	# if queue is empty, set current job as head
			self.head = Node(job, None)
		else:
			while (current != None) and (current.job.priorityClass != numClasses):			# insert at front of last class
				previous = current 				# prev = node[i]
				current = current.nextNode 		# current = node[i+1]
			
			# Insert new node after previous (before current)
			if (previous == None):
				self.head = Node(job, current)
			else:
				previous.nextNode = Node(job, current)

		self.Size += 1
		#print "ENQUEUE JOB"		

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
			print "%s, class %s, ERPT = %.4f"%(current.job.name, current.job.priorityClass, current.job.ERPT)
			current = current.nextNode


	def countClassesQueued(self, numClasses):
		if(LinkedList.Count == 0):
			LinkedList.NumJobArrayByClass = [0] * (numClasses + 1)	# create array that holds number of jobs in each classes

		# Iterate through number of classes and count number of jobs per class
		for j in range(1, numClasses + 1):
			current = self.head
			while (current != None):
				if current.job.priorityClass == j:
					LinkedList.NumJobArrayByClass[j] += 1
				elif current.job.priorityClass > numClasses:
					LinkedList.NumJobArrayByClass[numClasses] += 1
				current = current.nextNode
		return LinkedList.NumJobArrayByClass


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
		self.priorityClass = 100
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
	AvgNumJobsArray = []
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

		MachineClass.NextRoutedTo[:] = []


		MachineClass.PrevTime = 0
		MachineClass.PrevTimeA = 0
		MachineClass.PrevNumJobs = 0
		MachineClass.AvgNumJobs = 0		
		MachineClass.PrevNumJobsArray[:] = []
		MachineClass.AvgNumJobsArray[:] = []
		MachineClass.counter = 0

		NumJobs[:] = []
		NumJobsTime[:] = []
		TimeSys[:] = []
		ProcTime[:] = []
		PercError[:] = [] 
	
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
		for index in range(NUM_SERVERS):
			if(MachineClass.ProcessingJobs[index] != None):
				serviceTime = MachineClass.CurrentTime - MachineClass.ServiceStartTimes[index]
				MachineClass.ProcessingJobs[index].RPT -= serviceTime
				MachineClass.ProcessingJobs[index].ERPT -= serviceTime

	def saveArrivals(self, job):
		text = "%s,%.6f,%.6f,%.6f,%s,%.6f"%(job.name, job.arrivalTime, job.RPT, job.ERPT, job.priorityClass, job.completionTime) + "\n"
		
		with open("Jobs.txt", "a") as myFile:
			myFile.write(text)
		myFile.close()

	# Give arriving job a class and add it to the queue
	def assignClass(self, numClasses, job, prevJobs, counterStart, counter):
		# Remove oldest job from previous jobs list if there are too many
		while len(prevJobs) > (numClasses - 1):
			#print "prev jobs too long"
			prevJobs.pop(0)

		# Sort previous current job with previous jobs
		self.SortedPrevJobs = []
		self.SortedPrevJobs = list(prevJobs) 	# copy of prev jobs
		self.SortedPrevJobs.append(job)			# append current job (not a copy)
		self.SortedPrevJobs.sort(key=lambda JobClass: JobClass.ERPT)

		iterator = 1
		for j in self.SortedPrevJobs:
			if j.name == job.name:
				job.priorityClass = counterStart + counter
			counter += iterator

		# Regardless of class, append job to the general prev jobs list
		MachineClass.PreviousJobs.append(job)


	# Router sends job to servers and adds job to their queue
	# Compare to server last routed to of the same class, send to next one
	def router(self, job, numClasses):
		# Set up last routed to once
		servers = cycle(range(0, NUM_SERVERS))
		if(self.ctr == 0):
			MachineClass.NextRoutedTo = [0] * numClasses

			for item in range(len(MachineClass.NextRoutedTo)):
				MachineClass.NextRoutedTo[item] = next(servers)			# List of last server jobs sent to from each class
																		# Starts with each class routing to a different server
																		# Class 0 routes to server 0, class 1 routes to server 1...
			self.sendJobToServer(job, 0, numClasses)					#First job is always Class 0, so update for next arrival																
			MachineClass.NextRoutedTo[0] += 1
			
			# Return server id job is routed to
			return 0

		else:
			# For each priority class, if the incoming job matches the iterator, 
			for priorityClass in range(len(MachineClass.NextRoutedTo)):
				if (job.priorityClass == priorityClass):
					#Send job to the next server
					serverID = MachineClass.NextRoutedTo[priorityClass]
					self.sendJobToServer(job, serverID, numClasses)
					

					MachineClass.NextRoutedTo[priorityClass] += 1						# Update where we have routed to so as to go to next server next time.
			
					if(MachineClass.NextRoutedTo[priorityClass] > (NUM_SERVERS-1)):		# Reset after full loop of servers
						MachineClass.NextRoutedTo[priorityClass] = 0	

					# Return server id job is routed to
					return serverID
					
					


	# Send job to server i
	def sendJobToServer(self, job, i, numClasses):
	#GUI.writeToConsole(self.master, "sending %s to server %s"%(job.name, i))
	##	FOR EACH QUEUE, 
		# If job is in the last class, sort by LCFS
		if (job.priorityClass == numClasses):
			MachineClass.ServerQueues[i].insertByLCFS(job, numClasses);

		else:
			# Add current job with new class to queue 
			MachineClass.ServerQueues[i].insertByClass(job)				# add job to queue
		
		print "\n\n" + str(MachineClass.CurrentTime) + "::::::::::::::::::::::::::::::::::::" #+ str(MachineClass.NextRoutedTo)


	def calcNumJobs(self, jobID):
		self.currentNumJobs = MachineClass.Queue.Size
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


	def calcNumJobsPerClass(self, numClasses):
		numJobsArray = list(MachineClass.Queue.countClassesQueued(numClasses))

		self.t = MachineClass.CurrentTime 
		self.delta_t = self.t - MachineClass.PrevTimeA

		for i in range(0, numClasses):
			# If one job in system
			if(MachineClass.counter == 0):
				MachineClass.PrevNumJobsArray = [0] * (numClasses) 			# creates array of size (numClasses + 1) filled with 0s
				MachineClass.AvgNumJobsArray = list(numJobsArray)			# First event is always create new job
				MachineClass.counter = 1
			# UPDATE 
			else:
				MachineClass.AvgNumJobsArray[i] = (float(MachineClass.PrevTimeA)/self.t)*float(MachineClass.AvgNumJobsArray[i]) + float(MachineClass.PrevNumJobsArray[i])*(float(self.delta_t)/self.t)
									
		# PrevTime becomes "old" t (set in regular caclulation)
		MachineClass.PrevTimeA = self.t 
		# PrevNum jobs becomes current num jobs
		MachineClass.PrevNumJobsArray = list(numJobsArray)

	def saveNumJobs(self, currentTime, avgNumJobs, load, errorMin, errorMax):
		text = "%.6f,%.6f"%(currentTime, avgNumJobs) + "\n"

		if (abs(errorMin) == errorMax):
			self.error = str(int(errorMax))
		else:
			self.error = str(int(errorMin)) + "_" + str(int(errorMax))
		
		with open("NumJobs_numServers=%s_load=%s_alpha=%s_error=%s.xls"%(NUM_SERVERS, load, JobClass.BPArray[0], self.error), "a") as myFile:
			myFile.write(text)
		myFile.close()		

	def saveArrivals(self, job, load, errorMin, errorMax):
		text = "%s,%.6f,%.6f,%.6f,%s"%(job.name, job.arrivalTime, job.RPT, job.ERPT, job.priorityClass) + "\n"
	
		if (abs(errorMin) == errorMax):
			self.error = str(int(errorMax))
		else:
			self.error = str(int(errorMin)) + "_" + str(int(errorMax))	
		
		with open("Arrivals_numServers=%s_load=%s_alpha=%s_error=%s.xls"%(NUM_SERVERS, load, JobClass.BPArray[0], self.error), "a") as myFile:
			myFile.write(text)
		myFile.close()		

	def saveJobs(self, job, load, errorMin, errorMax):
		text = "%s,%.6f"%(job.name, job.completionTime) + "\n"
	
		if (abs(errorMin) == errorMax):
			self.error = str(int(errorMax))
		else:
			self.error = str(int(errorMin)) + "_" + str(int(errorMax))

		with open("Jobs_numServers=%s_load=%s_alpha=%s_error=%s.xls"%(NUM_SERVERS, load, JobClass.BPArray[0], self.error), "a") as myFile:
			myFile.write(text)
		myFile.close()		

	# Job arriving
	def arrivalEvent(self, load, arrDist, procRate, procDist, numClasses, percErrorMin, percErrorMax):
		J = JobClass(self.master)
		J.setJobAttributes(load, procRate, procDist, percErrorMin, percErrorMax, MachineClass.CurrentTime)
		J.name = "Job%02d"%self.ctr
		

		#self.calcNumJobs(self.ctr)
		#self.calcNumJobsPerClass(numClasses)

		self.assignClass(numClasses, J, MachineClass.PreviousJobs, 0, 0)	# Give job a class, and add to queue
		serverID = self.router(J, numClasses)								# Send job to a server queue

		GUI.writeToConsole(self.master, "%.6f | %s arrived, class = %s, server = %s"%(MachineClass.CurrentTime, J.name, J.priorityClass, serverID))		

		self.updateJobs()		# update all processing jobs

		procJob = MachineClass.ProcessingJobs[serverID]

		# Preempt processing job at server if new job has higher priority class
		if (procJob != None):
			if (J.priorityClass < procJob.priorityClass):
				GUI.writeToConsole(self.master, "%.6f | %s preempting %s"%(MachineClass.CurrentTime, J.name, procJob.name))

				#Remove procJob from processing
				MachineClass.ServersBusy[serverID] = False
				MachineClass.ProcessingJobs[serverID] = None
				MachineClass.ServiceStartTimes[serverID] = None

				# Add preempted job back to queue
				# If job is in the last class, sort by LCFS
				if (procJob.priorityClass == (numClasses - 1)):
					MachineClass.ServerQueues[serverID].insertByLCFS(procJob, numClasses);
					#GUI.writeToConsole(self.master, "%.6f | %s added back to server %s by lcfs, class = %s"%(MachineClass.CurrentTime, procJob.name, serverID, procJob.priorityClass))

				else:
					# Add current job with new class to queue 
					MachineClass.ServerQueues[serverID].insertByClass(procJob)				# add job to queue
					#GUI.writeToConsole(self.master, "%.6f | %s added back to server %s  by class, class = %s"%(MachineClass.CurrentTime, procJob.name, serverID, procJob.priorityClass))
				

		self.saveNumJobs(MachineClass.CurrentTime, MachineClass.AvgNumJobs, load, percErrorMin, percErrorMax)
		self.saveArrivals(J, load, percErrorMin, percErrorMax)
		self.processJobs(procJob)		# process first job in each queue

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
				GUI.writeToConsole(self.master, "%.6f | %s processing on server %s"%(MachineClass.CurrentTime, currentJob.name, serverID))
				MachineClass.ServerQueues[serverID].removeHead()

	# Job completed
	def completionEvent(self, numClasses, completingJob, load, percErrorMin, percErrorMax):
		completingJob.completionTime = MachineClass.CurrentTime
		self.saveJobs(completingJob, load, percErrorMin, percErrorMax)			# save to list of arrivals, for testing

		#self.calcNumJobs(self.ctr)
		#self.calcNumJobsPerClass(numClasses)

		# Server no longer busy
		serverID = MachineClass.ProcessingJobs.index(completingJob)
		MachineClass.ServersBusy[serverID] = False
		MachineClass.ProcessingJobs[serverID] = None
		MachineClass.ServiceStartTimes[serverID] = None

		TimeSys.append(MachineClass.CurrentTime - completingJob.arrivalTime)
		ProcTime.append(completingJob.procTime)
		PercError.append(abs(completingJob.percentError))

		GUI.writeToConsole(self.master, "%.6f | %s COMPLTED at server %s"%(MachineClass.CurrentTime, completingJob.name, serverID))

		if (MachineClass.ServerQueues[serverID].Size > 0):
			self.processJobs()


	def run(self, numServers, load, arrDist, procRate, procDist, percErrorMin, percErrorMax, numClasses, simLength):
		while 1:
			# Generate time of first job arrival
			if(self.ctr == 0):
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
				self.arrivalEvent(load, arrDist, procRate, procDist, numClasses, percErrorMin, percErrorMax)

			#next event is job finishing (job with shortest RPT)			
			else:
				completingJob = minProcJob
				MachineClass.CurrentTime += completingJob.RPT

				self.completionEvent(numClasses, completingJob, load, percErrorMin, percErrorMax)

			# If current time is greater than the simulation length, end program
			if (MachineClass.CurrentTime > simLength) or (MachineClass.StopSim == True):
				break



#----------------------------------------------------------------------#
def main():
	window = GUI(None)                           			   # instantiate the class with no parent (None)
	window.title('Multi-Server Approximate SRPT with Errors')  # title the window

	# Global variables used in JobClass
	main.timesClicked = 0       
	main.customEquation = ""

	#window.geometry("500x600")                     # set window size
	window.mainloop()                               # loop indefinitely, wait for events


if __name__ == '__main__': main()
