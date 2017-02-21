import pygame.camera
import pygame.image
import sys
import threading
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from SocketServer import ThreadingMixIn
import time
import urlparse
import Image
import base64
import numpy as np
import cv2
import json
import socket
import StringIO

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier('haarcascade_eye.xml')

IsRunnig = True

UseAuth = True 

AuthKey = None

serverport = 8080


HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

def printc(string,color):
    print color + string + ENDC

#Get list of webcams and start each one
pygame.camera.init()
cameras = pygame.camera.list_cameras()
cams = []
for c in range(len(cameras)):
    ca = pygame.camera.Camera(cameras[c])
    ca.start()
    printc("Turn on Camera %s ..." % cameras[c], OKGREEN)
    cams.append(ca)





class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

def FaceDetect(img):
	imgArr = np.asarray(img)
	gray = cv2.cvtColor(imgArr, cv2.COLOR_BGR2GRAY)
	faces = face_cascade.detectMultiScale(gray, 1.3, 5)
	
	#add face counter
	#w, h = img.size
	#cv2.putText(imgArr,('Faces: %s' % len(faces)),(w/h,h/15), cv2.FONT_HERSHEY_SIMPLEX, 1,(255,0,0),2)


	for (x,y,w,h) in faces:
	    cv2.rectangle(imgArr,(x,y),(x+w,y+h),(255,0,0),1)
	    roi_gray = gray[y:y+h, x:x+w]
	    roi_color = imgArr[y:y+h, x:x+w]
        '''
	    eyes = eye_cascade.detectMultiScale(roi_gray)
	    for (ex,ey,ew,eh) in eyes:
	        cv2.rectangle(roi_color,(ex,ey),(ex+ew,ey+eh),(0,0,0),1)
        '''
	return Image.fromarray(imgArr)

def sendAuth(self):
	self.send_response(401)
	self.send_header('WWW-Authenticate', 'Basic realm=\"ServerCam\"')
	self.send_header('Content-type', 'text/html')
	self.end_headers()

def checkAuth(self):
	global AuthKey
	if self.headers.getheader('Authorization') == None:
		sendAuth(self)
		self.wfile.write('no auth header received')
		return False
	elif self.headers.getheader('Authorization') == 'Basic ' + AuthKey:
		return True
	else:
		sendAuth(self)
		self.wfile.write(self.headers.getheader('Authorization'))
		self.wfile.write('not authenticated')
		return False


class CamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global cams, UseAuth
       
       	if (UseAuth == True):
        	if (checkAuth(self) == False):
				return

   		
        urlp = urlparse.urlparse(self.path)
        #keep_blank_values=True to dont remove ?cam=1&gray
        query_components = urlparse.parse_qs(urlp.query) 
        path = urlp.path

        if ('cam' in query_components):
            port = int(query_components['cam'][0])
            try:
                self.usecam = cams[port];
            except IndexError:
            	self.wfile.write('Cam not exists')
            	return

        if (path == '/list'):
            self.send_response(200)
            self.send_header('Content-type','text/text')
            self.end_headers()
            import json
            self.wfile.write(json.dumps({'count':len(cams),'cams':cameras}))
            return

       
        if (len(query_components) < 1):
	        self.wfile.write('Please use query [/?cam=0&q=50&gray=true&crop=2]')
	        return   

        self.send_response(200)
        self.send_header('Cache-Control', 'no-store, no-cache, private, max-age=0')
        self.send_header('Content-type','multipart/x-mixed-replace; boundary=--frame')
        self.send_header('Pragma', 'no-cache')
        self.end_headers()


        while IsRunnig:
            try:
                self.wfile.write("--frame")
                img = self.usecam.get_image()
                data = pygame.image.tostring(img, 'RGBA')
                aimg = Image.frombytes('RGBA', img.get_size(), data)


                if ('face' in query_components):
                	aimg = FaceDetect(aimg)

                if ('gray' in query_components):
                	#make image gray
                	aimg = aimg.convert('L') 

                #crop need to be after all if we want to use face detection
                if ('crop' in query_components):
                	w,h = img.get_size()
                	CropPr = int(query_components['crop'][0])
                	aimg = aimg.resize((w / CropPr, h / CropPr), Image.ANTIALIAS)

                '''
				Old function to chnage quality (look like it eat my cpu)
                if ('q' in query_components):
	                oa = StringIO.StringIO()
	                aimg.save(oa,'JPEG',quality=int(query_components['q'][0]))
	                oa.seek(0)
	                aimg = Image.open(oa)
	            '''

                self.send_header('Content-type','image/jpeg')
               	if ('q' in query_components):
                	o = StringIO.StringIO()
                	aimg.save(o,'JPEG',quality=int(query_components['q'][0]))
                	self.send_header('Content-length',str(o.len))
                	self.end_headers()
                	self.wfile.write(o.getvalue()) #after comp
                else:
                	self.send_header('Content-length',str(len(aimg.tobytes()))) #len(data) = len(aimg.tobytes()) #original image
                	self.end_headers()
                	aimg.save(self.wfile, 'JPEG') #original image
                self.wfile.write('\n')

     

            except Exception as e:
                pass
        return 



def buildKey(username,password):
	return base64.b64encode(username+':'+password)


def LoadConfig():
	global UseAuth
	global AuthKey
	global serverport
	try:
		data = json.loads(open('config.json','UTF-8').read())
		serverport = int(data['port'])
		if (data['auth']['allow']):
			UseAuth = True
			AuthKey = buildKey(data['auth']['username'],data['auth']['password'])
		else:
			UseAuth = False
		print 'Config load successfully'
	except:
		print 'Cant load config'
		UseAuth = True
		serverport = 8080
		AuthKey = buildKey('admin','admin')
		print 'Default username and password: admin,admin'


def GetLocalIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("gmail.com",80))
    PCip = s.getsockname()[0]
    s.close()
    return PCip

def main():
    global img
    global server
    global IsRunnig
    global serverport
    try:
        #ThreadedHTTPServer -> HTTPServer

       
        LoadConfig()
        PCip = GetLocalIp()
    

        
        server = ThreadedHTTPServer(('', serverport), CamHandler)

        print "Server start on http://"+PCip+':'+str(serverport)+'/'
        server.serve_forever()
    except KeyboardInterrupt:
        IsRunnig = False
        server.server_close()
        server.socket.close()
        sys.exit()
        

if __name__ == '__main__':
    main()
