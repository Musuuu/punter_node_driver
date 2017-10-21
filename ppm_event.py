#! /usr/bin/python
import os
import wiringpi as w
import time
import sys
import time
import threading
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
#----------------------------------------------------------------------
#----------------------------------------------------------------------
#----------------------------------------------------------------------
#----------------------------------------------------------------------

class MyHandler(PatternMatchingEventHandler):

    patterns = ["*.mpp"]

    def process(self, event):
        """
        event.event_type
            'modified' | 'created' | 'moved' | 'deleted'
        event.is_directory
            True | False
        event.src_path
            path/to/observed/file
        """
        # the file will be processed there
        print event.src_path, event.event_type  # print now only for degug
	f=open(event.src_path,"r")
	lines=f.read().split("\n")
	f.close()
	for l in lines:
		if len(l)> 1 :
			key,par =l.split(" ")
			if key == "init" :
				if locals().has_key("self.motor") == False :
					print "init"
					l1,l2,l3,l4=par.split(",")
					self.motor=stepper(int(l1),int(l2),int(l3),int(l4))
			elif key == "mov" :
				print "move"
				speed,target,dir=par.split(",")
				self.motor.move(int(speed),int(target),int(dir))
			elif key == "vel" :
				print "vel"
				time.sleep(1)
			elif key == "acc" :
				print "acc"
				time.sleep(1)
			elif key == "break" :
				print "break"
				time.sleep(1)
			elif key == "stop"  :
				print "stop"
				self.motor.stop()
				time.sleep(1)
	

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)
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
		self.acc= 500  # passi
		self.dec= 500  # passi 
		self.actspeed=0
		self.t=threading.Thread(target=self.update_pos)
		self.t.start()
		time.sleep(1)
		self.update=False

	def get_numstep(self):
		return self.numstep

	def stop(self):
		w.digitalWrite(self.inp[0],0)
		w.digitalWrite(self.inp[1],0)
		w.digitalWrite(self.inp[2],0)
		w.digitalWrite(self.inp[3],0)
		self.update=False
		

	def update_stop (self):
		self.update_run=False

	def update_pos (self):
	 	self.update= True
		self.update_run=True
		while self.update_run:
			if self.update :
				os.system("echo %d > /var/www/html/node/pos.dat" % (self.get_numstep()))
#				print "1"
			time.sleep(0.5)
#			print "2"

	def move (self,speed,rel=1,dir=1): #speed = passi al secondo Hz 
		self.update=True
		if dir >=0 :
			d=1
		else:
			d=-1
		refspeed=speed
		self.actspeed=1
		if rel <= (self.dec*2) :
			dec=rel/2	
		else:
			dec = self.dec
		for s in range(0,rel):
			self.numstep=self.numstep+d
			if s == (rel - dec) :
				refspeed = 0
			t=1.0/self.actspeed
			actacc=float(speed)/self.acc
			print self.numstep,1.0/self.actspeed,self.actspeed,actacc,speed
			fase=self.numstep  % 8
			for k in range(0,4):
#				print k, self.inp[k],self.half[fase][k]
				w.digitalWrite(self.inp[k],self.half[fase][k])
			if self.actspeed < refspeed :
				print "Acc"
				self.actspeed=self.actspeed+ actacc
				if self.actspeed > speed :
					self.actspeed = speed

			elif self.actspeed > refspeed :
				print "Dec"
				self.actspeed=self.actspeed - actacc
				if self.actspeed <= 0 :
					self.actspeed = 0.001
					return
			time.sleep(t)
		time.sleep(1)
		self.update=False
#--------------------------------------------------------------------------------
#----------------------------------------------------------------------
if __name__ == '__main__':
    args = sys.argv[1:]
    observer = Observer()
#    observer.schedule(MyHandler(), path="./")
    observer.schedule(MyHandler(), path="/var/www/html/node/")
    observer.start()
    time.sleep(1)
    try:
	os.system("cp /var/www/html/node/motor.init /var/www/html/node/motor.mpp")
	time.sleep(1)
	os.system("echo 'stop 0' > /var/www/html/node/motor.mpp")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
#----------------------------------------------------------------------
#motor1=stepper(7,0,2,3)
#while 1:
#	motor1.move(2000,8192,1)
#	motor1.move(1500,8192,-1)
