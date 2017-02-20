# CamStream
Stream your webcams over http using mjpeg format

###### [*] Basic authentication [admim,admin]
###### [*] Face detection
###### [*] Multiple webcams
###### [*] Image compression (quality, crop, grayscale)
###### [*] Config File

## Endpoints
###### [*] /?cam=(int)
###### [*] /list -> Show list of your connected webcams



## Url query
###### [*] example url: http://localhost:8080/?cam=0&q=50&gray=true&crop=2
###### [*] cam=(int) 
###### [*] q=(int)
###### [*] gray=(bool)
###### [*] crop=(int) -> image size / crop
###### [*] face=(bool)

## Config File
###### [*] Want to disable basic auth -> In config.json change auth:allow to False
###### [*] Want to change basic auth username and password -> In config.json change auth:username & auth:password
![alt tag](https://raw.githubusercontent.com/avramit/CamStream/master/screenshot.png)
