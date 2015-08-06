#----------------------------------------------------------------------#
# main.py
#
# This application simulates a single server with Poisson arrivals
# and processing times of a general distribution. There are errors in
# time estimates within a range. Arrivals are assigned to SRPT classes
# using the methods described in Adaptive and Scalable Comparison Scheduling.
#
# Note: This program uses Simpy 3.0.x. To switch back 'pip install "simpy>=2.3,<3"'
#
# Rachel Mailach
#----------------------------------------------------------------------#

import simpy
from Tkinter import *
from datetime import datetime
from math import exp, log
import random
import ttk
import tkMessageBox
import tkFileDialog

NumJobs = []
TimeSys = []
ProcTime = []
PercError = []

#----------------------------------------------------------------------#
# Class: GUI
#
# This class is used as a graphical user interface for a larger
# application.
#
#----------------------------------------------------------------------#
class GUI(Tk):
	def __init__(self, master):
		Tk.__init__(self, master)
		self.master = master        # reference to parent
		self.statusText = StringVar()
		random.seed(datetime.now())

		# create the input frame
		self.frameIn = Input(self)
		#self.frameIn.grid(row = 0, column = 0, padx = 5, pady =5, ipadx = 5, ipady = 5)
		self.frameIn.pack(side=TOP, fill=BOTH, padx = 5, pady =5, ipadx = 5, ipady = 5)		

		# create the output frame
		self.frameOut = Output(self)
		#self.frameOut.grid(row = 1, column = 0, padx = 5, pady =5, ipadx = 5, ipady = 5)
		self.frameOut.pack(side=TOP, fill=BOTH, padx = 5, pady =5, ipadx = 5, ipady = 5)

		# bind simulate button
		self.bind("<<input_simulate>>", self.submit)

		# bind save button
		self.bind("<<output_save>>", self.saveData)

		# bind clear button
		self.bind("<<output_clear>>", self.clearConsole)

		# Status Bar
		status = Label(self.master, textvariable=self.statusText, bd=1, relief=SUNKEN, anchor=W)
		#status.grid(row=10, column=0, columnspan=10) # row at very large number, so always at bottom
		status.pack(side=BOTTOM, anchor=W, fill=X)		

		# initialize console
		self.makeConsole()
		self.printIntro()
		self.updateStatusBar("Waiting for submit...")

	def makeConsole(self):
		consoleFrame = Frame(self.frameOut)
		consoleFrame.pack(side=TOP, padx=5, pady=5)
		self.console = Text(consoleFrame, wrap = WORD)
		self.console.config(state=DISABLED) # start with console as disabled (non-editable)
		scrollbar = Scrollbar(consoleFrame)
		scrollbar.config(command = self.console.yview)
		self.console.config(yscrollcommand=scrollbar.set)
		self.console.grid(column=0, row=0)
		scrollbar.grid(column=1, row=0, sticky='NS')

	def writeToConsole(self, text = ' '):
		self.console.config(state=NORMAL) # make console editable
		self.console.insert(END, '%s\n'%text)
		self.update()
		self.console.config(state=DISABLED) # disable (non-editable) console

	def saveData(self, event):
		# get filename
		filename = tkFileDialog.asksaveasfilename(title="Save as...", defaultextension='.txt')
		
		if filename:
			file = open(filename, mode='w')
			data = self.console.get(1.0, END)
			encodedData = data.encode('utf-8')
			text = str(encodedData)
		
			file.write(text)
			file.close()

	def clearConsole(self, event):
		self.console.config(state=NORMAL) # make console editable
		self.console.delete('1.0', END)
		self.console.config(state=DISABLED) # disable (non-editable) console

	def updateStatusBar(self, text=' '):
		self.statusText.set(text)

	def printIntro(self):
		self.writeToConsole("Approximate SRPTE \n\n This application simulates a single server with Poisson arrivals and 			processing times of a general distribution. Each arrival has an estimation error within a percent error taken as 			input. Arrivals are assigned to SRPT classes using the methods described in Adaptive and Scalable Comparison 			Scheduling.")

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
		AvgNumJobs = int(float(sum(NumJobs))/len(NumJobs))
		AvgTimeSys = float(sum(TimeSys))/len(TimeSys)
		AvgProcTime = float(sum(ProcTime))/len(ProcTime)
		VarProcTime = self.calcVariance(ProcTime, AvgProcTime)
		AvgPercError = float(sum(PercError))/len(PercError)

		self.writeToConsole('\n\nSINGLE SERVER SRPT')
		self.writeToConsole('Average number of jobs in the system %s' %AvgNumJobs)
		self.writeToConsole('Average time in system, from start to completion is %s' %AvgTimeSys)
		self.writeToConsole('Average processing time, based on generated service times is %s' %AvgProcTime)
		self.writeToConsole('Variance of processing time %s' %VarProcTime)
		self.writeToConsole('Average percent error %.4f\n' %AvgPercError)
		#self.writeToConsole('Request order: %s' % ArrivalClass.JobOrderIn)
		self.writeToConsole('Service order: %s\n\n\n' % ServerClass.JobOrderOut)

	def submit(self, event):
		self.updateStatusBar("Simulating...")
		inputInstance = Input(self)

		self.printParams(inputInstance.valuesList[0], inputInstance.valuesList[1],\
				 inputInstance.valuesList[2], inputInstance.valuesList[3],\
				 inputInstance.valuesList[4])

		main.timesClicked = 0
		env = simpy.Environment()
       		resource = simpy.PriorityResource(env, capacity=1) 


		A = ArrivalClass(env, self)
       		arrivalProcess = env.process(A.generateArrivals(env, inputInstance.valuesList[0], 'Poisson',\
						inputInstance.valuesList[1], inputInstance.distList[1],\
						inputInstance.valuesList[2], inputInstance.valuesList[3], resource))

		env.run(until=inputInstance.valuesList[4])
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
	#valuesList = []

	def __init__(self, master):
		LabelFrame.__init__(self, master, text = "Input")
		self.master = master
		self.arrivalRateInput = DoubleVar()
		self.processingRateInput = DoubleVar()
		self.percentErrorInput = DoubleVar()
		self.numberOfClassesInput = IntVar()
		self.simLengthInput = DoubleVar()

		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(0, weight=1)

		# Labels
		labels = ['Interarrival Rate (' + u'\u03bb' + ')', 'Processing Rate (' + u'\u03bc' + ')', '% Error', 'Number of Classes', 'Simulation Length']
		r=0
		c=0
		for elem in labels:
			Label(self, text=elem).grid(row=r, column=c)
			r=r+1
		Label(self, text=u"\u00B1").grid(row=2, column=1)

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



		# Simulate Button
		self.simulateButton = Button(self, text = "SIMULATE", command = self.onButtonClick)
		self.simulateButton.grid(row = 5, columnspan = 4)

		# Distribution Dropdowns
		self.distributions = ('Select Distribution', 'Exponential', 'Uniform', 'Custom')
		#self.comboBox_1 = ttk.Combobox(self, values = self.distributions, state = 'readonly')
		#self.comboBox_1.current(0) # set selection
		#self.comboBox_1.grid(row = 0, column = 2)
		self.comboBox_2 = ttk.Combobox(self, values = self.distributions, state = 'readonly')
		self.comboBox_2.current(1) # set default selection 					#####################CHANGE LATER
		self.comboBox_2.grid(row = 1, column = 3)


	def onButtonClick(self):
		self.getNumericValues()
		self.getDropDownValues()

		# send to submit button in main
		self.simulateButton.event_generate("<<input_simulate>>")

	def getNumericValues(self):
		arrivalRate = self.arrivalRateInput.get()
		processingRate = self.processingRateInput.get()
		percentError = self.percentErrorInput.get()
		numberOfClasses = self.numberOfClassesInput.get()
		maxSimLength = self.simLengthInput.get()

		if arrivalRate <= 0.0: tkMessageBox.showerror("Input Error", "Arrival rate must be non-zero value!")
		if processingRate <= 0.0: tkMessageBox.showerror("Input Error", "Processing rate must be non-zero value!")
		if maxSimLength <= 0.0: tkMessageBox.showerror("Input Error", "imulation length must be non-zero value!")

		Input.valuesList = [arrivalRate, processingRate, percentError, numberOfClasses, maxSimLength]
		return Input.valuesList

	def getDropDownValues(self):
		#if self.comboBox_1.get() == 'Select Distribution': print "Box 1 has to have a selection"
		if self.comboBox_2.get() == 'Select Distribution': GUI.writeToConsole(self.master, "You must select a distribution for the processing rate")

		Input.distList = ["", self.comboBox_2.get(), "", "", ""]
		return Input.distList


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
		self.clearButton = Button(buttonFrame, text = "CLEAR ALL DATA", command = self.onClearButtonClick)
		self.clearButton.grid(row = 2, column = 0)
		
		# Save Button
		self.saveButton = Button(buttonFrame, text = "SAVE ALL DATA", command = self.onSaveButtonClick)
		self.saveButton.grid(row=2, column=1)

	def onClearButtonClick(self):
		# clear console
		self.clearButton.event_generate("<<output_clear>>")

	def onSaveButtonClick(self):
		# save data
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

		#Button frame
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
# Class: ArrivalClass
#
# This class is used to generate Jobs at random.
#
#----------------------------------------------------------------------#
class ArrivalClass(object):
	def __init__(self, env, master):
		self.env = env
		self.master = master

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

	def sortQueue(self, numClasses):
		#grab the previous m (splitMech = numClasses - 1) jobs to sort jobs by estimated processing time (procTime) 
		ServerClass.Queue[-(numClasses):] = sorted(ServerClass.Queue[-(numClasses):], key=lambda JobClass: JobClass.estimatedProcTime) 
		return ServerClass.Queue
	
	def generateArrivals(self, env, arrRate, arrDist, procRate, procDist, percError, numClasses, server):
		while 1:
			# wait for arrival of next job
			yield env.timeout(self.setArrivalDist(arrRate, arrDist))

			J = JobClass(self.env, self.master)
			J.setJobAttributes(procRate, procDist, percError)
			J.name = "Job%02d"%self.ctr
			
			# add job to queue
			ServerClass.Queue.append(J)

			GUI.writeToConsole(self.master, "%.6f | %s arrived, estimated proc time = %s"%(self.env.now, J.name, J.estimatedProcTime))
			#GUI.writeToConsole(self.master, "\nREMAINING QUEUE LENGTH: %d "%len(ServerClass.Queue) + str([job.name for job in ServerClass.Queue]))

			# sort jobs
			self.sortQueue(numClasses)

			S = ServerClass(self.env, self.master)
			serverProcess = env.process(S.executeJobs(server))

			self.ctr += 1


#----------------------------------------------------------------------#
# Class: JobClass
#
# This class is used to define jobs.
#
#----------------------------------------------------------------------#
class JobClass(object):
	def __init__(self, env, master):
		self.env = env
		self.master = master
		self.arrivalTime = self.env.now
		self.realProcTime = 0

	# dictionary of service distributions
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



	# generates a percent error for processing time
	def generateError(self, percError):
		self.percentError = pow(-1, random.randint(0,1)) * (percError * random.random())
		return self.percentError

	def setJobAttributes(self, procRate, procDist, percError):
		# generate processing time for the job
		self.realProcTime = self.setServiceDist(procRate, procDist)
		self.estimatedProcTime = (1 + (self.generateError(percError)/100.0))*self.realProcTime			


#----------------------------------------------------------------------#
# Class: ServerClass
#
# This class is used to actually model the job processing.
#
#----------------------------------------------------------------------#
class ServerClass(object):
	NumJobsInSys = 0
	CompletedJobs = 0
	Queue = [] 		# jobs queued for the machines
	JobOrderOut = []

	def __init__(self, env, master):
		self.env = env
		self.master = master

	def executeJobs(self, server):
		ServerClass.NumJobsInSys += 1

		# first job in queue requests service
		# "with" statement automatically releases the resource when it has completed its job
        	with server.request() as req:
			GUI.writeToConsole(self.master, "%.6f | %s requests service, estimated proc time = %s"%(self.env.now, ServerClass.Queue[0].name, ServerClass.Queue[0].estimatedProcTime))
			yield req
		
			# job is removed from queue, ready to start executing
			Job = ServerClass.Queue.pop(0)
			GUI.writeToConsole(self.master, "%.6f | %s server request granted, begin executing"%(self.env.now, Job.name))
		
			# process job according to REAL processing time
			yield self.env.timeout(Job.realProcTime)

			# job completed and released
			GUI.writeToConsole(self.master, "%.6f | %s COMPLETED"%(self.env.now, Job.name))
			ServerClass.JobOrderOut.append(Job.name)	

		ServerClass.NumJobsInSys -= 1

		NumJobs.append(ServerClass.NumJobsInSys)
		TimeSys.append(self.env.now - Job.arrivalTime)
		ProcTime.append(Job.realProcTime)
		PercError.append(abs(Job.percentError)) # only take absolute value of error


#----------------------------------------------------------------------#
def main():
	window = GUI(None)                          	# instantiate the class with no parent (None)
	window.title('Single Server Approximate SRPT with Errors')  # title the window

	#global variables used in JobClass
	main.timesClicked = 0		
	main.customEquation = ""

	#window.geometry("500x600")                     # set window size
	window.mainloop()                               # loop indefinitely, wait for events


if __name__ == '__main__': main()
