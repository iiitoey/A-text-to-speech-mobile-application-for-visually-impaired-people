#For Develop

from flask import Flask,request
from flask_restful import Api, Resource
import json
import pytesseract
import re
import cv2
import numpy as np
from pythainlp.util import normalize
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

def trim_str(raw_txt):
    #Check space ระหว่างข้อความ
    new_txt = ''
    for i in range(len(raw_txt)):
        if ord(raw_txt[i]) != 32:
            new_txt += raw_txt[i]
        elif ord(raw_txt[i+1]) < 3585:
            new_txt += raw_txt[i]
   
    #ลบ \n \t   
    new_txt = ' '.join(new_txt.split())
    new_txt = normalize(new_txt)
    new_txt = re.sub('[\/\~\_\:\«\|\<\+\*\/\|\>\<\;\¥\»\§\¢\©\°]','',new_txt)
    new_txt = re.sub('[๐]','',new_txt)
    
    return new_txt

#Api
app = Flask(__name__)
api = Api(app)


#Get
class getThaiOCR(Resource):
    def get(self):
        filename = 'Data\data.json'
        #Read File
        with open(filename,"r") as file:
            data = json.load(file)
        return data
    
#Post
class thaiOCR(Resource):
    def post(self):
        language = request.form["language"]
        img = request.files["image"]
        
        ############### Read Filename return Id ####################
        # Read File
        filename = 'Data\data.json'
        with open(filename, "r") as file:
            data = json.load(file)
            # print(data[0]["userId"])
            userId = 0
            for i in range(len(data)):
                userId = data[i]["userId"]
            userId += 1
            # print(userId)
        
        ################# Save Photo ######################################
        img.save("Imgfrompost.jpg")
        imgPath = "Imgfrompost.jpg"
        
        ################## Image Processing #################
        originalImg = cv2.imread(imgPath)
        grayImg = cv2.cvtColor(originalImg, cv2.COLOR_BGR2GRAY)
        #thresh,th1 = cv2.threshold(grayImg,128,255,cv2.THRESH_BINARY)
        adaptiveThresh = cv2.adaptiveThreshold(grayImg,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,85,11) 
        kernel = np.ones((1,1), np.uint8)
        dilation = cv2.dilate(adaptiveThresh,kernel,iterations=1)
        erosion = cv2.erode(dilation,kernel,iterations=1)
        
        cv2.imwrite("Preprocessing\\"+str(language)+"\\"+str(language)+str(userId)+".jpg",erosion) 

        ############# Optical Character Recognition ########################
        if language == "eng":
            BeforeCleanText = pytesseract.image_to_string(erosion)
        elif language == "thai": 
            BeforeCleanText = pytesseract.image_to_string(erosion, lang ='tha')
        elif language == "engthai":
            BeforeCleanText = pytesseract.image_to_string(erosion,lang='eng+tha')
            
            
        ############# Clean Text #########################################
        CleanText = trim_str(BeforeCleanText)
       
        
        ############## SAVE TO DATA ########################################
        namePhoto = language+str(userId)+".jpg"
        writeToJsonFile(userId,namePhoto,language,BeforeCleanText,CleanText)
        
        return {"data": CleanText} 
        
        
# บันทึกลงไฟล์json Camera
def writeToJsonFile(userId,namePhoto,language,BeforeCleanText,CleanText):
    filename = 'Data\data.json'
    entry = {"userId": userId,
             "namePhoto":namePhoto,
             "language":language,
             "BeforeCleanText":BeforeCleanText,
             "CleanText":CleanText}
    
    # Read File
    with open(filename, "r") as file:
        data = json.load(file)
    # Update json Object
    data.append(entry)
    # Write json file
    with open(filename, "w") as file:
        json.dump(data, file, ensure_ascii=False)


api.add_resource(getThaiOCR, "/ocr")
api.add_resource(thaiOCR, "/ocr")

if __name__ == "__main__":
    app.run(debug=True)