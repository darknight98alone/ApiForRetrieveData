import argparse
import pytesseract
from PIL import Image
from PyPDF2 import PdfFileReader
from imutils import contours
from pdf2image import convert_from_path
import skew
import DetectTable
import handleTable
import os
import imutils
import cv2
from docx import Document
from PdfToImages import pdfToImage

def handleFile(fileName,deblur=False,handleTableBasic=True,handleTableAdvance=False):
    """
    :param fileName: name of image to be converted
    :param outputName: name of doc file to be saved
    :return:

    detect table and layout-analyzing
    """
    img = cv2.imread(fileName)
    # handle skew
    img = skew.skewImage(img)
    # skew.printImage(img)
    # handle table with not auto fill
    if handleTableBasic or handleTableAdvance:
        if handleTableBasic:
            mask = DetectTable.detectTable(img).run(1)
        else:
            mask = DetectTable.detectTable(img).run(2)
        # maskName = "mask.jpg"
        # mask_img = cv2.imread(maskName)
        mask_img = mask
        print(mask.shape)
        ## resize
        listResult, listBigBox = handleTable.getTableCoordinate(mask_img)
        img = cv2.resize(img, (mask_img.shape[1], mask_img.shape[0]))
        # origin = img.copy()
        resultTable = handleTable.retreiveTextFromTable(listResult,img)
        for pt in listBigBox:
            (x, y, w, h) = pt
            if w > 0.9*img.shape[1]:
                continue
            # cv2.rectangle(img,(x,y),(x+w,y+h),(0,0,0),2)
            img[y:(y + h - 1), x:(x + w - 1)] = 255
        # out, result = handleTable.process_par(img, origin, listBigBox) ## use for layout
    # skew.printImage(img)
    resultNotTable = pytesseract.image_to_string(img,lang="vie")
    return resultNotTable,resultTable

def saveResult(folder,saveFileName,result):
    file  = os.path.join(folder,saveFileName)
    if os.path.exists(file):
        f = open(file,"a+")
    else:
        f = open(file,"w+")
    f.write(result)
    f.close()

def getFileName(fileType,folder):
    names = []
    if fileType == "pdf":
        count = 0
        for filename in os.listdir(folder):
            if "pdf" in filename:
                filename = os.path.join(folder,filename)
                count = pdfToImage(filename,folder) ## convert to image
        for k in range(1,count+1):
            names.append(str(k)+".jpg")
    else:
        listname = os.listdir(folder)
        if fileType == "image":
            for name in listname:
                if name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    names.append(name)
        elif fileType == "text":
            for name in listname:
                if name.lower().endswith(('.txt', '.doc', '.docx')):
                    names.append(name)
    return names

def preprocessFile(fileType,folder,saveFileName):
    names = getFileName(fileType,folder)
    result = ""
    if fileType == "pdf" or fileType == "image":
        for filename in names:
            filename = os.path.join(folder,filename)
            if ".jpg" in filename:
                resultNotTable,resultTable = handleFile(filename,deblur=False,handleTableBasic=True,handleTableAdvance=False)
                result= result + (str(resultNotTable))
                k = 0
                for rs in resultTable:
                    if k %4 == 0:
                        result = result + "\n"
                    result= result + (str(rs))+" "
                    k = k+ 1
                if fileType == "pdf":
                    os.remove(filename)
    elif fileType=="text":
        for filename in names:
            filename = os.path.join(folder,filename)
            f = open(filename,"r")
            result = result + str(f.read())
            f.close()
    if result != "":
        saveResult(folder,saveFileName,result)
    return result

if __name__ == '__main__':
    fileType = "pdf"## pdf, docx, jpg, txt
    folderContainsFile = "./save/"
    fileTextToSave = "text.txt"
    resultString = preprocessFile(fileType,folderContainsFile,fileTextToSave)
    print(resultString)