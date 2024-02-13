import cv2
from util import OverlayEngine
from util import imgH,imgW

recordFolder=r'C:\rris40data\FT027g\2021-10-01-09-48-29'    #please edit this line to point to the extracted folder.
cameraIndex=2      #select a number (0-7)

resizeFor1080pScreenOrSmaller=True
engine=OverlayEngine(recordFolder,cameraIndex)

while True:
    img=engine.getNextFrame()
    if img is None:
        break
    else:
        if resizeFor1080pScreenOrSmaller:
            img=cv2.resize(img,(imgW//2,imgH//2))
        cv2.imshow('RRIS40 Viewer',img) #resize because the image is too large for normal 1080p screen
        key=cv2.waitKeyEx(1)
        if key==27: #Esc
            break

engine.close()