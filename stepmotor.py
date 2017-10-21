import wiringpi as w
import time
import threading
#----------------------------------------------------------------------
#----------------------------------------------------------------------
#----------------------------------------------------------------------
#----------------------------------------------------------------------
class stepper():

	def __init__(self,i1,i2,i3,i4):
		w.wiringPiSetup()
		self.inp=[i1,i2,i3,i4]
		w.pinMode(i1,w.OUTPUT)
		w.pinMode(i2,w.OUTPUT)
		w.pinMode(i3,w.OUTPUT)
		w.pinMode(i4,w.OUTPUT)
		w.digitalWrite(i1,0)
		w.digitalWrite(i2,0)
		w.digitalWrite(i3,0)
		w.digitalWrite(i4,0)
		self.numstep=0
		self.half=[]
		self.half.append([1,0,0,1]) # setp 0
		self.half.append([1,0,0,0]) # step 1
		self.half.append([1,1,0,0]) # step 2
		self.half.append([0,1,0,0]) # step 3
		self.half.append([0,1,1,0]) # step 4
		self.half.append([0,0,1,0]) # step 5
		self.half.append([0,0,1,1]) # step 6
		self.half.append([0,0,0,1]) # step 7
		self.acc= 1000  # passi
		self.dec= self.acc  # passi 
		self.actspeed=0

	def stop (self):
		w.digitalWrite(self.inp[0],0)
		w.digitalWrite(self.inp[2],0)
		w.digitalWrite(self.inp[3],0)
		w.digitalWrite(self.inp[1],0)
		
	def move (self,speed,rel=1,dir=1): #speed = passi al secondo Hz 
		if dir >=0 :
			d=1
		else:
			d=-1
		refspeed=speed
		self.actspeed=1
		dec=self.dec
		if rel <= self.dec :
			dec = rel/2
		for s in range(0,rel):
			self.numstep=self.numstep+d
			if s == rel-dec :
				refspeed = 0
			t=1.0/self.actspeed
			actacc=speed/self.acc
			print self.numstep,1.0/self.actspeed
			fase=self.numstep  % 8
			for k in range(0,4):
#				print k, self.inp[k],self.half[fase][k]
				w.digitalWrite(self.inp[k],self.half[fase][k])
			if self.actspeed < refspeed :
				print "+ 100"
				self.actspeed=self.actspeed+ actacc
				if self.actspeed > speed :
					self.actspeed = speed

			elif self.actspeed > refspeed :
				print "- 100"
				self.actspeed=self.actspeed - actacc
				if self.actspeed < 0 :
					self.actspeed = 0
					return
			time.sleep(t)
#--------------------------------------------------------------------------------
#----------------------------------------------------------------------
#----------------------------------------------------------------------
motor1=stepper(7,0,2,3)
while 1:
	motor1.move(2000,4096/2,1)
	motor1.stop()
	time.sleep(2)
	motor1.move(2000,4096/2,-1)
	motor1.stop()
	time.sleep(2)
