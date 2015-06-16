#----------------------------------------------------------------------#
# main.py
#  
# This application simulates a single server with Poisson arrivals 
# and processing times of a general distribution. There are errors in
# time estimates within a range. Arrivals are assigned to SRPT classes
# using the methods described in Adaptive and Scalable Comparison Scheduling.
# 
# Rachel Mailach
#----------------------------------------------------------------------#

from SimPy.Simulation import *
from Tkinter import *
from datetime import datetime
from random import seed,Random,expovariate,uniform,normalvariate # https://docs.python.org/2/library/random.html
import ttk


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
		
		self.master = master		# reference to parent
		random.seed(datetime.now())

		# create the input frame
		self.frameIn = Input(self)
		self.frameIn.grid(row = 0, column = 0, padx = 5, pady =5, ipadx = 5, ipady = 5)

		# create the output frame
		self.frameOut = Output(self)
		self.frameOut.grid(row = 1, column = 0, padx = 5, pady =5, ipadx = 5, ipady = 5)

		# bind simulate button
		self.bind("<<input_simulate>>", self.submit)

		# initialize console
		self.makeConsole()

	def makeConsole(self):
		self.console = Text(self.frameOut, wrap = WORD)
		self.console.config(state=DISABLED)	# start with console as disabled (non-editable)
		scrollbar = Scrollbar(self.frameOut)
		scrollbar.config(command = self.console.yview)
		self.console.config(yscrollcommand=scrollbar.set)
		self.console.grid(column=0, row=0)
		scrollbar.grid(column=1, row=0, sticky='NS')

	def writeToConsole(self, text = ' '):
		self.console.config(state=NORMAL) # make console editable
		self.console.insert(END, '%s\n'%text)
		self.update()
		self.console.config(state=DISABLED)	# disable (non-editable) console

	def clearConsole(self):
#		self.console.config(state=NORMAL) # make console editable
		self.console.delete('1.0', END)
#		self.console.config(state=DISABLED)	# disable (non-editable) console


	#COPIED THIS FUNCTION, MAKE IT MY OWN
	def findMonitors(self):
		self.monitors = []
		for k in self.__dict__:
			a = self.__dict__[k]
			if isinstance(a, list) and hasattr(a, 'tseries') and hasattr(a, 'yseries'):
				self.monitors.append(a)

	#COPIED THIS FUNCTION, MAKE IT MY OWN
	def displayData(self):
		self.findMonitors()
		for i in self.monitors:
			self.writeToConsole('Monitor \'%s\':\n' % i.name)
			dat = i
			try: 
				xlab = i.tlab
			except:
				xlab = 'x'
			try:
				ylab = i.ylab
			except:
				ylab = 'y'
			sep = ',\t'
			self.writeToConsole('%s%s%s' % (xlab, sep, ylab))
			for this in dat:
				self.writeToConsole('%s%s%s' % (this[0],sep, this[1]))

	def DisplayData(self):
		self.writeToConsole('SINGLE SERVER SRPT')
		self.writeToConsole('Average number in the system is %s' %m.timeAverage())
		self.writeToConsole('Average time in system is %s' %mT.mean())
		self.writeToConsole('Actual average service-time is %s' %msT.mean())

	def submit(self, event):
		#self.frameOut.GetOutputList()
		#self.clearConsole()
		self.writeToConsole("--------------------------------------------------------------------------------")
		self.writeToConsole("Simulation begun\n")
		
		m = Monitor() # monitor for number of jobs
		mT = Monitor() # monitor for time in system
		msT = Monitor() # monitor for generated service times
		
		server=Resource(capacity=1, name='Processor')

		inputInstance = Input(self)
		initialize()
		A = ArrivalClass(self)
		activate(A, A.Run())
		m.observe(0)		# number in system is 0 at the start
		simulate(until=inputInstance.valuesList[3])

		self.DisplayData()		

		self.writeToConsole("\nSimulation complete\n")



#----------------------------------------------------------------------#
# Class: Input
#  
# This class is used as a graphical user interface for a larger
# application.
# 
#----------------------------------------------------------------------#
class Input(LabelFrame):
	valuesList = []

	def __init__(self, parent):
		LabelFrame.__init__(self, parent, text = "Input")

		#self.arrivalRate = 0.0
		#self.processingRate = 0.0
		#self.percentError = 0.0
		#self.simLength = 0.0
		
		self.arrivalRateInput = DoubleVar()
		self.processingRateInput = DoubleVar()
		self.percentErrorInput = DoubleVar()
		self.simLengthInput = DoubleVar()

		# create widgets, parent = self because window is parent
		# Labels	
		labels = [u'\u03bb', u'\u03bc', '% error     ' u"\u00B1", 'simulation length']
		r=0
		c=0
		for elem in labels:
			Label(self, text=elem).grid(row=r, column=c)
			r=r+1
			if r > 3:
				r=0
				c=3
			
		# Entry Boxes
		self.entry_1 = Entry(self, textvariable = self.arrivalRateInput)
		self.entry_2 = Entry(self, textvariable = self.processingRateInput)
		self.entry_3 = Entry(self, textvariable = self.percentErrorInput)
		self.entry_4 = Entry(self, textvariable = self.simLengthInput)

		# Simulate Button
		self.simulateButton = Button(self, text = "SIMULATE", command = self.OnButtonClick)

		self.distributions = ('Select Distribution', 'Exponential', 'Normal', 'Custom')

		#self.comboBox_1 = ttk.Combobox(self, values = self.distributions, state = 'readonly')
		#self.comboBox_1.current(0) # set selection

		self.comboBox_2 = ttk.Combobox(self, values = self.distributions, state = 'readonly')
		self.comboBox_2.current(0) # set selection


		self.entry_1.grid(row = 0, column = 1)
		self.entry_2.grid(row = 1, column = 1)
		self.entry_3.grid(row = 2, column = 1)
		self.entry_4.grid(row = 3, column = 1)
		
		self.simulateButton.grid(row = 4, columnspan = 2)
	
		#self.comboBox_1.grid(row = 0, column = 2)
		self.comboBox_2.grid(row = 1, column = 2)

	def OnButtonClick(self):
		self.GetNumericValues()
		self.GetDropDownValues()

		# send to submit button in main
		self.simulateButton.event_generate("<<input_simulate>>")	
			

	def GetNumericValues(self):
		arrivalRate = self.arrivalRateInput.get()
		processingRate = self.processingRateInput.get()
		percentError = self.percentErrorInput.get()
		maxSimLength = self.simLengthInput.get()	

		if arrivalRate <= 0.0: GUI.writeToConsole(self.master, "Arrival rate has to be non-zero!")
		if processingRate <= 0.0: GUI.writeToConsole(self.master, "Processing rate has to be non-zero!")
		if percentError <= 0.0: GUI.writeToConsole(self.master, "Percent error has to be non-zero!")
		if maxSimLength <= 0.0: GUI.writeToConsole(self.master, "Simulation length has to be non-zero!")

		Input.valuesList = [arrivalRate, processingRate, percentError, maxSimLength]
		return Input.valuesList
		
	def GetDropDownValues(self):
		#if self.comboBox_1.get() == 'Select Distribution': print "Box 1 has to have a selection"
		if self.comboBox_2.get() == 'Select Distribution': GUI.writeToConsole(self.master, "You must select a distribution for the processing rate")

		Input.distList = ["", self.comboBox_2.get(), "", ""]
		return Input.distList

	def CreateList(self):
		InputList = zip(Input.valuesList, Input.distList)
		return InputList


#----------------------------------------------------------------------#
# Class: Output
#  
# This class is used as a graphical user interface for a larger
# application.
#
#----------------------------------------------------------------------#
class Output(LabelFrame):
	def __init__(self, parent):
		LabelFrame.__init__(self, parent, text = "Output")	


#----------------------------------------------------------------------#
# Class: JobClass
#  
# This class is used to actually model the job processing.
#
#----------------------------------------------------------------------#
class JobClass(Process):
	#Busy = []	# busy machines
	#Idle = []	# idle machines
	#Queue = []	# queued for the machines
	#IdlingTime = 0.0
	#JobServiceTime = 0.0
	#SystemMon = Monitor()
	#QueueMon = Monitor()
	NumJobsInSys = 0

	def __init__(self, master):
		Process.__init__(self)
		#MachineClass.Idle.append(self)	# starts idle
		self.master = master
		self.inputInstance = Input(self.master)
	
		#---------------------------------------------------------------
		#serviceMonitor = Monitor(name = 'Service Times')
		#serviceMonitor.xlab = 'Time'
		#serviceMonitor.ylab = 'Total service time = wait + service'
		#---------------------------------------------------------------
	
		ProcessingDistributions =  {
			'Exponential': random.expovariate(self.inputInstance.valuesList[1])
			#'Normal': Rnd.normalvariate(self.ServiceRate)
			#'Custom':
		}

		#self.generateError()  #########later put on each processing time
		
	# dictionary of service distributions
	def SetServiceDist(self):
		return Globals.ServiceDistributions[Globals.ServiceDist]

	# generates a percent error for processing time	
	def generateError(self):
		self.percentError = pow(-1, random.randint(0,1)) * (self.inputInstance.valuesList[2] * random.random()) 
		GUI.writeToConsole(self.master, "\nGenerated Error: %.4f"%self.percentError)
		
	def Run(self):
		#while 1:
			arrTime = now()
			JobClass.NumInSys += 1
			m.observe(JobClass.NumInSys)
			
			yield request,self,server
		
			#next arrival time?
			nextArrival = expovariate(1.0/self.inputInstance.valuesList[3])
			msT.observe(nextArrival)
			yield hold, self, nextArrival #process for this amount of time?

			# job completed, release
			yield release, self, server
			JobClass.NumInSys -= 1
			m.observe(JobClass.NumInSys)
			mT.observe(now() - arrTime)
			
			# sleep until this machine awakened
			#yield passivate, self
			#MachineClass.Idle.remove(self)
			#MachineClass.Busy.append(self)

			# take next job in queue
			#while MachineClass.Queue != []:
			#	Job = MachineClass.Queue.pop(0)			# get job
			#	TotalQueuedTime = now() - Job.ArrivalTime	# time spent between job arrival, and just before job is serviced
			#	MachineClass.QueueMon.observe(TotalQueuedTime)
				#MachineClass.QueueMon.tally(TotalQueuedTime)
			#	yield hold,self, self.SetServiceDist()	# service the job
			#	TotalTimeInSystem = now() - Job.ArrivalTime			# time spent between job arrival, and job completion
			#	MachineClass.SystemMon.observe(TotalTimeInSystem) 
				#MachineClass.SystemMon.tally(TotalTimeInSystem)
	#-------------------------------------------------------------------
			#	MachineClass.serviceMonitor.observe(now() - Job.ArrivalTime)
	#-------------------------------------------------------------------
		
			#MachineClass.Busy.remove(self)
			#MachineClass.Idle.append(self)

			GUI.writeToConsole(self.master, "Customer leaves at ", now())

#----------------------------------------------------------------------#
# Class: JobClass
#  
# This class simulates the jobs.
#
#----------------------------------------------------------------------#
#class JobClass:			
#	def __init__(self):
#		self.ArrivalTime = now()
		#print now(), "Event: Job arrives and joins the queu"


#----------------------------------------------------------------------#
# Class: ArrivalClass
#  
# This class is used to generate Jobs at random.
#
#----------------------------------------------------------------------#
class ArrivalClass(Process):
	def __init__(self, master):
		Process.__init__(self)
		self.master = master
		self.inputInstance = Input(self.master)
#		self.Rnd = Random(12345)
		self.printParams()

		ArrivalDistributions = {
			'Exponential': random.expovariate(self.inputInstance.valuesList[0])
			#'Normal': Rnd.normalvariate(self.inputInstance.valuesList[0])
			#'Custom':
		}

	def printParams(self):
		GUI.writeToConsole(self.master, "\nPARAMETERS:")
		GUI.writeToConsole(self.master, "Arrival Rate = %.4f"%self.inputInstance.valuesList[0])
		GUI.writeToConsole(self.master, "Processing Rate = %.4f"%self.inputInstance.valuesList[1])
		GUI.writeToConsole(self.master, "% Error  = " + u"\u00B1" + " %.4f"%self.inputInstance.valuesList[2])
		GUI.writeToConsole(self.master, "Simulation Length = %.4f"%self.inputInstance.valuesList[3])

	# Dictionary of arrival distributions
	#def SetArrivalDist(self):
	#	return ArrivalDistributions[self.inputInstance.valuesList[1])

	def Run(self):
		#global waitMonitor, serviceMonitor
		#GUI.waitMon = waitMonitor = Monitor(name = 'Wait Times')
		#waitMonitor.tlab = 'Time'
		#waitMonitor.ylab = 'Customer waiting time'

		counter = 0
		while 1:
			A = JobClass(self)
			activate(A,A.Run(self.inputInstance.valuesList[1]), delay=0) # activate over mean service time #####################

			# wait for arrival of next job			
			##yield hold, self, self.SetArrivalDist()							
			yield hold, self, random.expovariate(self.inputInstance.valuesList[0]) # only exponential for this application
					
			#MachineClass.Queue.append(Job)

			# check if any machines are idle and ready for work
			#if MachineClass.Idle != []:
			#	reactivate(MachineClass.Idle[0])
			counter += 1



#----------------------------------------------------------------------#
def main():
	window = GUI(None)							# instantiate the class with no parent (None)
	window.title('Single Server SRPT with Errors')	# title the window	
	#window.geometry("500x600")						# set window size


	window.mainloop()								# loop indefinitely, wait for events


if __name__ == '__main__': main()


