"""
@author:    Kukheon Lee
@contact:   kukheon1109@gmail.com
"""

import os, sys
import json
from os import listdir
from os.path import isfile, join
from multiprocessing import Pool 
sys.path.insert(0, "/READ/PDF")

from PDF.carpe_pdf import PDF
from OOXML.Carpe_OOXML import OOXML
from MS_Office.carpe_compound import Compound

filePath = "C:\\Users\\kukheon\\Desktop\\test"

def push_analysis(file):
    #print(file + ' ★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆ 분석시작')
    target = os.path.join(filePath, file)
    nameChk, extChk = os.path.splitext(target)

    print(file + ' ★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆★☆ ' + file)

    if extChk in '.pdf': #pdf 파일처리
        with PDF(target) as pdf:
            pdf.parse_content()
    elif extChk in ('.doc', '.xls', '.ppt'): #COMPOUND
        object = Compound(target) 
        object.parse()
    elif extChk in ('.docx', '.xlsx', '.pptx'): 
        object = OOXML(target)
        object.parse_ooxml()
    elif extChk in '.hwp': 
        print('hwp')
    
    #with open("C:\\Users\\kukheon\\Desktop\\output\\" + file+'.json', 'w', encoding='utf-8') as jsonOutput:
        #jsonOutput.write(pdf.content)

def get_filelist():
    rtFileList =  [f for f in listdir(filePath) if isfile(join(filePath, f))]
    return rtFileList

if __name__ == "__main__":

    pool = Pool(processes=4)
    pool.map(push_analysis, get_filelist())
    print('END')
