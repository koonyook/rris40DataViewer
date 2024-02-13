import pickle
import cv2
import numpy as np
import datetime

imgW,imgH=1920,1200
aspectRatio=imgW/imgH

def cleanFolderPath(path):  #clean folder path from glob to become my convention, don't use with file path
    path=path.replace('\\','/')
    if path[-1]!='/':
        path+='/'
    return path

class SequentialVideoReader:
    def __init__(self,videoPath):
        self.cap=cv2.VideoCapture(videoPath)    #.avi
    
    def getNextFrame(self):
        ret,frame=self.cap.read()
        return frame
    
    def close(self):
        self.cap.release()

class MarkerRecord:

    def __init__(self,filepath):
        self.markerNameList = []
        self.record = []
        self.frameNo = []
        self.timestamp = []	 #in second 
        self.event = []	#tuple of (name,frame,time)
        counter=0

        f=open(filepath,'r')    #this file pointer will be closed after the read is done
        while(True):
            line=f.readline()
            if(line==''):
                f.close()
                break
            else:
                s=line.strip().split('\t')
                if(s[0]=="NO_OF_FRAMES"):
                    pass
                elif(s[0]=="NO_OF_CAMERAS"):
                    pass
                elif(s[0]=="NO_OF_MARKERS"):
                    pass
                elif(s[0]=="FREQUENCY"):
                    self.frequency=float(s[1])  #important
                elif(s[0]=="NO_OF_ANALOG"):
                    pass
                elif(s[0]=="ANALOG_FREQUENCY"):
                    pass
                elif(s[0]=="DESCRIPTION"):
                    self.description=s[1]
                elif(s[0]=="TIME_STAMP"):		#TESTED
                    #TIME_STAMP	2021-01-08, 20:34:56.157	111711.00139370
                    #the first section is starting time
                    #the second section is number of seconds since the computer was started.
                    date,time=s[1].split(',')
                    time=time.strip()
                    year,month,day=date.split('-')
                    hour,minute,second=time.split('.')[0].split(':')
                    self.startTime=datetime.datetime(int(year),int(month),int(day),int(hour),int(minute),int(second),0)
                elif(s[0]=="DATA_INCLUDED"):
                    pass
                elif(s[0]=="EVENT"):
                    self.event.append((s[1],int(s[2]),float(s[3])))
                elif(s[0]=="MARKER_NAMES"):	#read all marker's name
                    self.markerNameList=s[1:]
                    #log.debug(self.markerNameList)
                elif(s[0]=="Frame" and s[1]=="Time"):		#header above each column
                    pass
                elif(s[0]=="TRAJECTORY_TYPES"):         #new version of QTM export tsv with this non-meaningful line
                    pass
                else:
                    if(len(s)>len(self.markerNameList)*3):	#frame number and time in the first 2 columns
                        self.frameNo.append(int(s[0]))
                        self.timestamp.append(float(s[1]))
                        numbers=s[2:]
                    else:	#no frame number and timestamp info
                        numbers=s
                    
                    row={}
                    for i,markerName in enumerate(self.markerNameList):
                            if(numbers[i*3+0]=="NULL" and numbers[i*3+1]=="NULL" and numbers[i*3+2]=="NULL"):
                                continue	#just skip this marker (normally happen at the early or late frame)
                            else:
                                row[markerName]=np.array([
                                    float(numbers[i*3+0])/1000,
                                    float(numbers[i*3+1])/1000,
                                    float(numbers[i*3+2])/1000
                                ])
                    self.record.append(row)

        self.firstFrameNo=self.frameNo[0]   #this is not index, don't be confused
        self.firstFrameIndex=self.firstFrameNo-1
        if self.firstFrameNo>1:   #this record is cropped
            fillerSize=self.firstFrameNo-1
            self.record = [{}]*fillerSize + self.record
            self.frameNo = [None]*fillerSize + self.frameNo
            self.timestamp = [None]*fillerSize + self.timestamp

    def getMarkerTrajectory(self,markerName):
        ans=[]
        for rowDict in self.record:
            if markerName in rowDict:
                ans.append(rowDict[markerName])
            else:
                ans.append(None)
        return ans
    
triggerToStartExposureTime=0.00006969
    
exposureTable={
     0 :0.786415,
    -1 :0.499823,
    -2 :0.249907,
    -3 :0.124951,
    -4 :0.062470,
    -5 :0.031186,
    -6 :0.015588,
    -7 :0.007787,
    -8 :0.003888,   
    -9 :0.001992,
    -10:0.000996,   
    -11:0.000492,
    -12:0.000192,
    -13:0.000096,
    -14:0.000048,
}

def getHalfExposure(exposure):  
    #exposure can be from 0 to -13
    return exposureTable[exposure]/2

def getTimeFromRaisingEdgeIndex(risingEdgeIndex,halfExposure,camPeriod):  #for gcam only
    return risingEdgeIndex*camPeriod + triggerToStartExposureTime + halfExposure + 0.001170 

def interpolateFromQualisys(qualisys_pt,qualisysFrequency,t):   #qualisys_pt is a list of 3D position or None
    qualisysPeriod=1/qualisysFrequency

    qLeftIndex = int(t//qualisysPeriod)
    qRightIndex = qLeftIndex+1
    
    if 0<=qRightIndex<len(qualisys_pt):
        if(qualisys_pt[qLeftIndex] is not None and qualisys_pt[qRightIndex] is not None):
            qRealIndex = t/qualisysPeriod
            rightRatio = qRealIndex-qLeftIndex
            leftRatio = 1-rightRatio
            return qualisys_pt[qLeftIndex]*leftRatio+qualisys_pt[qRightIndex]*rightRatio   #(3,)
        else:
            return None
    else:
        return None

def project(qualisysFrame_points,camCalibDict):
    #projection is in UV order
    #return in (n,2) shape
    #rvec and tvec used with this function are calculated from camFrame_labFrame, don't be confused.
    return cv2.projectPoints(qualisysFrame_points, camCalibDict['rvec'], camCalibDict['tvec'], camCalibDict['K'], camCalibDict['D'])[0][:,0,:]

def paintCrossThick(img,pxUV,r=10,color=[0,255,0]):
    v=int(round(pxUV[1]))
    u=int(round(pxUV[0]))
    if 0+1<=v<imgH-1 and 0+1<=u<imgW-1:
        color=np.array(color,dtype=np.uint8).reshape([1,3])
        for d in [-1,0,1]:
            img[v+d,u-r:u+r+1,:]=color
            img[v-r:v+r+1,u+d,:]=color

class OverlayEngine:
    def __init__(self,recordFolder,camIndex):
        recordFolder=cleanFolderPath(recordFolder)

        metadataPath=recordFolder+'metadata.pkl'
        with open(metadataPath,'rb') as f:
            metaDict=pickle.load(f)

        camIdList=metaDict['camIdList']
        camId=camIdList[camIndex]
        nF=metaDict['frameCountList'][camIndex]

        calibPath=recordFolder+'systemCalibration.pkl'
        with open(calibPath,'rb') as f:
            systemCalib=pickle.load(f)

        #load tsv
        tsvPath=recordFolder+'qualisys.tsv'
        mr=MarkerRecord(tsvPath)
        qualisysPeriod=1/mr.frequency

        #precalculate projection
        halfExposure=getHalfExposure(metaDict['exposure'])

        qualisysFrequencyDivisor=metaDict['qualisysFrequencyDivisor']
        camPeriod=qualisysPeriod*qualisysFrequencyDivisor
        print('Pre-calculating projection...')
        uv={}  #markerName,frame
        for markerName in mr.markerNameList:    #slow because there are so many markers
            uv[markerName]={}
            traj=mr.getMarkerTrajectory(markerName)   #list of None or (3,) #this is fast
            
            project_uv=[]
            project_inCircle=[]
            for ri in range(nF):
                t=getTimeFromRaisingEdgeIndex(ri,halfExposure,camPeriod)
                qPoint=interpolateFromQualisys(traj, mr.frequency, t)

                if qPoint is None:
                    project_uv.append(None)
                    project_inCircle.append(False)
                    continue
                else:
                    qUV=project(qPoint,systemCalib[camId])[0,:]
                    
                    if 0<=qUV[0]<imgW and 0<=qUV[1]<imgH:
                        project_uv.append(qUV)  #(2,)
                    else:
                        project_uv.append(None)

            uv[markerName]=project_uv

        self.uv=uv
        videoPath=recordFolder+'keepMarker'+camId+'.h264'
        self.vReader=SequentialVideoReader(videoPath)
        self.nF=nF
        self.currentFrameIndex=0

    def getNextFrame(self):
        if self.currentFrameIndex>=self.nF-1:
            return None

        img=self.vReader.getNextFrame()

        #overlay
        for markerName in self.uv.keys():
            tmpUV=self.uv[markerName][self.currentFrameIndex]
            if tmpUV is not None:
                paintCrossThick(img,tmpUV,15,[0,255,0])               
        self.currentFrameIndex+=1
        return img

    def close(self):
        self.vReader.close()