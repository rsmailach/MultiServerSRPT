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
from random import Random,expovariate,uniform,normalvariate # https://docs.python.org/2/library/random.html
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
		self.initialize()

	def initialize(self):
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

	def submit(self, event):
		#self.frameOut.GetOutputList()
		#self.clearConsole()
		self.writeToConsole("--------------------------------------------------------------------------------")
		self.writeToConsole("Simulation begun\n")
		
		self.sim = Simulation(self)


#----------------------------------------------------------------------#
# Class: Input
#  
# This class is used as a graphical user interface for a larger
# application.
# 
#----------------------------------------------------------------------#
class Input(LabelFrame):
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
		self.arrivalRate = self.arrivalRateInput.get()
		self.processingRate = self.processingRateInput.get()
		self.percentError = self.percentErrorInput.get()
		self.maxSimLength = self.simLengthInput.get()	

		if self.arrivalRate <= 0.0: GUI.writeToConsole(self.master, "Arrival rate has to be non-zero!")
		if self.processingRate <= 0.0: GUI.writeToConsole(self.master, "Processing rate has to be non-zero!")
		if self.percentError <= 0.0: GUI.writeToConsole(self.master, "Percent error has to be non-zero!")
		if self.maxSimLength <= 0.0: GUI.writeToConsole(self.master, "Simulation length has to be non-zero!")

		Input.valuesList = [self.arrivalRate, self.processingRate, self.percentError, self.maxSimLength]
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
# Class: Simulation
#  
# This class is used to actually model the simmulation.
#
#----------------------------------------------------------------------#
class Simulation():
	def __init__(self, master):
		self.master = master
		self.inputInstance = Input(self.master)
		random.seed(datetime.now())
#		self.Rnd = Random(12345)
		self.printParams()
		self.generateError()  ###################################################################later put on each processing time

		ArrivalDistributions = {
			'Exponential': random.expovariate(self.inputInstance.valuesList[0])
			#'Normal': Rnd.normalvariate(self.inputInstance.valuesList[0])
			#'Custom':
		}
		ProcessingDistributions =  {
			'Exponential': random.expovariate(self.inputInstance.valuesList[1])
			#'Normal': Rnd.normalvariate(self.ServiceRate)
			#'Custom':
		}

	def printParams(self):
		GUI.writeToConsole(self.master, "\nPARAMETERS:")
		GUI.writeToConsole(self.master, "Arrival Rate = %.4f"%self.inputInstance.valuesList[0])
		GUI.writeToConsole(self.master, "Processing Rate = %.4f"%self.inputInstance.valuesList[1])
		GUI.writeToConsole(self.master, "% Error  = " + u"\u00B1" + " %.4f"%self.inputInstance.valuesList[2])
		GUI.writeToConsole(self.master, "Simulation Length = %.4f"%self.inputInstance.valuesList[3])

	def generateError(self):
		self.percentError = pow(-1, random.randint(0,1)) * (self.inputInstance.valuesList[2] * random.random()) 
		GUI.writeToConsole(self.master, "\nGenerated Error: %.4f"%self.percentError)
		


#----------------------------------------------------------------------#
def main():
	window = GUI(None)							# instantiate the class with no parent (None)
	window.title('Single Server SRPT with Errors')	# title the window	
	#window.geometry("500x600")						# set window size
	window.mainloop()								# loop indefinitely, wait for events


if __name__ == '__main__': main()

