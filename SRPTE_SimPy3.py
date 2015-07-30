#----------------------------------------------------------------------#
# SRPTE_SimPy3.py
#
# This application simulates a single server with Poisson arrivals
# and processing times of a general distribution. There are errors in
# time estimates within a range. Jobs are serviced in order of shortest 
# remaining processing time.
#
# Note: This program uses Simpy 3.0.x. To switch back 'pip install "simpy>=2.3,<3"'
#
# Rachel Mailach
#----------------------------------------------------------------------#

import simpy 
from Tkinter import *
from datetime import datetime
#from random import seed,Random,expovariate,uniform,normalvariate # https://docs.python.org/2/library/random.html
import random
from math import exp, log
import tkMessageBox
import ttk
import tkFileDialog
import csv
import operator

#----------------------------------------------------------------------#
# Class: G
#
# This class is used to store application globals.
#
#----------------------------------------------------------------------#
class G: 
	#now = datetime.now().second + datetime.now().microsecond
	interrupted = False
	resourceBusy = False

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
		self.frameIn.pack(side=TOP, fill=BOTH, padx = 5, pady =5, ipadx = 5, ipady = 5)		

		# create the output frame
		self.frameOut = Output(self)
		self.frameOut.pack(side=TOP, fill=BOTH, padx = 5, pady =5, ipadx = 5, ipady = 5)

		# bind simulate button
		self.bind("<<input_simulate>>", self.submit)

		# bind save button
		self.bind("<<output_save>>", self.saveData)

		# bind clear button
		self.bind("<<output_clear>>", self.clearConsole)

		# Status Bar
		status = Label(self.master, textvariable=self.statusText, bd=1, relief=SUNKEN, anchor=W)
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

	# Empty queue file at the begining of each simulation
	def clearQueueFile(self):
		open('SRPTE_Queue.txt', 'w').close()

	def clearConsole(self, event):
		self.console.config(state=NORMAL) # make console editable
		self.console.delete('1.0', END)
		self.console.config(state=DISABLED) # disable (non-editable) console

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

	def DisplayData(self):			
		self.writeToConsole('\n\nSINGLE SERVER SRPT')
		#self.writeToConsole('Average number of jobs in the system at any given time %s' %ArrivalClass.m.timeAverage())
		#self.writeToConsole('Average time in system, from start to completion is %s' %ArrivalClass.mT.mean())
		#self.writeToConsole('Average processing time, based on generated service times is %s' %ArrivalClass.msT.mean())
		#self.writeToConsole('Variance of processing time %s\n' %ArrivalClass.msT.var())
		self.writeToConsole('Request order: %s' % ArrivalClass.JobOrderIn)
		self.writeToConsole('Service order: %s\n\n\n' % ServerClass.JobOrderOut)

				
	def submit(self, event):
		self.updateStatusBar("Simulating...")
		self.clearQueueFile()
		inputInstance = Input(self)		

		self.printParams(inputInstance.valuesList[0], inputInstance.valuesList[1],\
				 inputInstance.valuesList[2], inputInstance.valuesList[3])

		main.timesClicked = 0
		env = simpy.Environment()
		resource = simpy.PreemptiveResource(env, capacity=1) 
		
		A = ArrivalClass(env, self)
		arrivalProcess = env.process(A.GenerateArrivals(env, inputInstance.valuesList[0], 'Poisson',\
								inputInstance.valuesList[1], inputInstance.distList[1],\
								inputInstance.valuesList[2], resource))

		#ArrivalClass.m.observe(0)        # number in system is 0 at the start
		
		# Start processes
		env.run(until=inputInstance.valuesList[3])
		self.DisplayData()
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
		self.simLengthInput = DoubleVar()

		self.approxSRPTE = IntVar()
		self.SRPTE = IntVar()
		self.PSBS = IntVar()
		self.approxSRPTE.set(1)
		self.SRPTE.set(1)
		self.PSBS.set(1)

		self.grid_columnconfigure(0, weight=1)
		self.grid_rowconfigure(0, weight=1)

		# Labels
		labels = ['Interarrival Rate (' + u'\u03bb' + ')', 'Processing Rate (' + u'\u03bc' + ')', '% Error' , 'Simulation Length']
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
		self.comboBox_2.current(1) # set default selection 					#####################CHANGE LATER
		self.comboBox_2.grid(row = 1, column = 3)

		# Simulate Button
		self.simulateButton = Button(self, text = "SIMULATE", command = self.OnButtonClick)
		self.simulateButton.grid(row = 7, columnspan = 4)

	def OnButtonClick(self):
		self.GetNumericValues()
		self.GetDropDownValues()
		self.GetCheckboxValues()

		# send to submit button in main
		self.simulateButton.event_generate("<<input_simulate>>")

	def GetNumericValues(self):
		arrivalRate = self.arrivalRateInput.get()
		processingRate = self.processingRateInput.get()
		percentError = self.percentErrorInput.get()
		maxSimLength = self.simLengthInput.get()

		if arrivalRate <= 0.0: tkMessageBox.showerror("Input Error", "Arrival rate must be non-zero value!")
		if processingRate <= 0.0: tkMessageBox.showerror("Input Error", "Processing rate must be non-zero value!")
		if maxSimLength <= 0.0: tkMessageBox.showerror("Input Error", "imulation length must be non-zero value!")

		Input.valuesList = [arrivalRate, processingRate, percentError, maxSimLength]
		return Input.valuesList

	def GetDropDownValues(self):
		#if self.comboBox_1.get() == 'Select Distribution': print "Box 1 has to have a selection"
		if self.comboBox_2.get() == 'Select Distribution': GUI.writeToConsole(self.master, "You must select a distribution for the processing rate")

		Input.distList = ["", self.comboBox_2.get(), "", "", ""]
		return Input.distList

	# gets 0 or 1 value for checkboxes
	def GetCheckboxValues(self):
		Input.simList = [self.approxSRPTE.get(), self.SRPTE.get(), self.PSBS.get()]
		return Input.simList

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
		self.clearButton = Button(buttonFrame, text = "CLEAR ALL DATA", command = self.OnClearButtonClick)
		self.clearButton.grid(row = 2, column = 0)
		
		# Save Button
		self.saveButton = Button(buttonFrame, text = "SAVE ALL DATA", command = self.OnSaveButtonClick)
		self.saveButton.grid(row=2, column=1)

	def OnClearButtonClick(self):
		# clear console
		self.clearButton.event_generate("<<output_clear>>")

	def OnSaveButtonClick(self):
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
	JobOrderIn = []

	def __init__(self, env, master):
		self.env = env
		self.master = master

		#ArrivalClass.m = Monitor() # monitor for number of jobs
		#ArrivalClass.mT = Monitor() # monitor for time in system
		#ArrivalClass.msT = Monitor() # monitor for generated service times

		# reset monitors 
		#ArrivalClass.m.reset()
		#ArrivalClass.mT.reset()
		#ArrivalClass.msT.reset()	
	
		self.ctr = 0

	# Dictionary of arrival distributions
	def SetArrivalDist(self, arrRate, arrDist):
		ArrivalDistributions = {
			'Poisson': random.expovariate(1.0/arrRate),
			'Exponential': random.expovariate(arrRate)
			#'Normal': Rnd.normalvariate(self.inputInstance.valuesList[0])
			#'Custom':
		}
		return ArrivalDistributions[arrDist]

	def AddJobToFile(self, job):
		text = str(job.name) + "," + str(job.arrivalTime) + "," + str(job.realRemainingProcTime) + "," + \
			str(job.estimatedRemainingProcTime) + "\n"
		
		with open("SRPTE_Queue.txt", "a") as myFile:
			myFile.write(text)
			myFile.close()

	def SortQueueFile(self):
		with open("SRPTE_Queue.txt", "r") as myFile:
			csv1 = csv.reader(myFile, delimiter=',')
			sort = sorted(csv1, key=operator.itemgetter(3)) #sort by 4th column (starts at 0)
			myFile.close()

		with open("SRPTE_Queue.txt", "w") as myFile:
			for eachline in sort:
				line = ','.join(eachline)	# convert each row to correct format
				myFile.write(line + '\n')
				print line
			myFile.close()
			print "\n"

	def GenerateArrivals(self, env, arrRate, arrDist, procRate, procDist, percError, server):
		while 1:
			# wait for arrival of next job
			yield env.timeout(self.SetArrivalDist(arrRate, arrDist))

			J = JobClass(self.env, self.master)
			J.SetJobAttributes(procRate, procDist, percError)
			J.name = "Job%02d"%self.ctr
			
			# add job to queue
			self.AddJobToFile(J)
			ArrivalClass.JobOrderIn.append(J.name)
			#ServerClass.Queue.append(J)

			GUI.writeToConsole(self.master, "%.6f | %s arrived, estimated proc time = %s"%(self.env.now, J.name, J.estimatedRemainingProcTime))
			
			S = ServerClass(self.env, self.master)


			# INTERRUPT JOB IN SERVICE (if not already interrupted), AND SORT QUEUE
			#if not G.interrupted:
			if G.resourceBusy:
				serverProcess.interrupt(J)

			serverProcess = env.process(S.ExecuteJobs(server))				

			self.ctr += 1

				# sort queue
				#self.SortQueueFile()


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
		self.procTime = 0
		self.priority = 0
		self.realRemainingProcTime = 0
		self.estimatedRemainingProcTime = 0

	# dictionary of service distributions
	def SetServiceDist(self, procRate, procDist):
		self.ServiceDistributions =  {
			'Exponential': self.SetExponDist,
			'Uniform': self.SetUniformDist,
			#'Normal': Rnd.normalvariate(self.ServiceRate)
			'Custom': self.SetCustomDist
		}
		return self.ServiceDistributions[procDist](procRate)

	def SetExponDist(self, procRate):
		return random.expovariate(procRate)

	def SetUniformDist(self, procRate):
		return random.uniform(0.0, procRate)

	def SetCustomDist(self, procRate):
		if main.timesClicked == 0:
			main.timesClicked += 1
        		self.popup=CustomDist(self.master)
        		self.master.wait_window(self.popup.top)
			main.customEquation = self.popup.stringEquation
		return eval(main.customEquation)

	# generates a percent error for processing time
	def GenerateError(self, percError):
		self.percentError = pow(-1, random.randint(0,1)) * (percError * random.random())
		return self.percentError

	def SetJobAttributes(self, procRate, procDist, percError):
		# generate processing time for the job
		self.procTime = self.SetServiceDist(procRate, procDist)
		self.estimatedProcTime = (1 + (self.GenerateError(percError)/100.0))*self.procTime
		self.realRemainingProcTime = self.procTime
		self.estimatedRemainingProcTime = self.estimatedProcTime		


#----------------------------------------------------------------------#
# Class: ServerClass
#
# This class is used to actually model the job processing.
#
#----------------------------------------------------------------------#
class ServerClass(object):
	NumJobsInSys = 0
	CompletedJobs = 0
	JobOrderOut = []

	def __init__(self, env, master):
		self.env = env
		self.master = master
		self.arrivalInstance = ArrivalClass(env, master)

	def GetFirstJobQueued(self):
		with open('SRPTE_Queue.txt', 'r') as myFile:
			reader = csv.reader(myFile)
			firstRow = next(reader)

			myFile.close()

		job = JobClass(self.env, self.master)

		job.name = str(firstRow[0])
		job.arrivalTime = float(firstRow[1])
		job.realRemainingProcTime = float(firstRow[2])
		job.estimatedRemainingProcTime = float(firstRow[3])
		job.priority = -job.estimatedRemainingProcTime		# Priority is negative of estimated remaining processing time, \
									# less processing time remaining equals higher priority
		return job

	def RemoveFirstJobQueued(self):
		with open('SRPTE_Queue.txt', 'r') as fin:
    			data = fin.read().splitlines(True)
			fin.close()
		with open('SRPTE_Queue.txt', 'w') as fout:
   			fout.writelines(data[1:])
			fout.close()
	

	def ExecuteJobs(self, server):
		ServerClass.NumJobsInSys += 1
		#ArrivalClass.m.observe(ServerClass.NumJobsInSys)

		# first job in queue requests service
		Job = self.GetFirstJobQueued()
		
		# This "with" statement automatically releases the resource when it has completed its job
		with server.request(priority=Job.priority) as req:
			GUI.writeToConsole(self.master, "%.6f | %s requests service"%(self.env.now, Job.name))
			try:
				yield req # request server
			except simpy.Interrupt:
				pass
				
			# job is ready to start executing
			G.resourceBusy = True
			serviceStartTime = self.env.now
			GUI.writeToConsole(self.master, "%.6f | %s server request granted"%(self.env.now, Job.name))
			#ArrivalClass.msT.observe(Job.realRemainingProcTime)
			try:
				yield self.env.timeout(Job.realRemainingProcTime)  # process job according to REAL processing time

			# Interrupted, update values
			except simpy.Interrupt as interrupt:
				#G.interrupted = True
				#newJob = "newJob" #interrupt.cause.by 
	
				# Job has had some processing time (may not yet be complete), update values
				serviceTime = self.env.now - serviceStartTime	
				Job.realRemainingProcTime -= serviceTime
				Job.estimatedRemainingProcTime -= serviceTime
				Job.priority = Job.estimatedRemainingProcTime

				GUI.writeToConsole(self.master, "%.6f | %s INTERRUPTED, rem proc time %s"%(self.env.now, Job.name, Job.estimatedRemainingProcTime))

				#sort queue
				self.arrivalInstance.SortQueueFile()
				#G.interrupted = False


		# Job completed and released
		G.resourceBusy = False
		GUI.writeToConsole(self.master, "%.6f | %s COMPLTED"%(self.env.now, Job.name))
		ServerClass.JobOrderOut.append(Job.name)
		self.RemoveFirstJobQueued()	

		ServerClass.NumJobsInSys -= 1
		#ArrivalClass.m.observe(ServerClass.NumJobsInSys)
		#ArrivalClass.mT.observe(now - Job.arrivalTime)





#----------------------------------------------------------------------#
def main():
	window = GUI(None)                          	# instantiate the class with no parent (None)
	window.title('Single Server SRPT with Errors')  # title the window

	#global variables used in JobClass
	main.timesClicked = 0		
	main.customEquation = ""

	#window.geometry("500x600")                     # set window size
	window.mainloop()                               # loop indefinitely, wait for events


if __name__ == '__main__': main()
