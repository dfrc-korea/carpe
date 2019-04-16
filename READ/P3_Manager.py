#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author:    Kukheon Lee
@contact:   kukheon1109@gmail.com
"""
import os, sys
from os import listdir
from os.path import isfile, join
sys.path.insert(0, "/READ/PDF")

#from READ.PDF.carpe_pdf import PDF
#from READ.OOXML.Carpe_OOXML import OOXML
from READ.MS_Office.carpe_compound import Compound

class IITP3:
    #각 모듈로 던져주기(+멀티프로세싱 처리 필요) 
    def ModuleSelect(self, fileX):
        nameChk, ext = os.path.splitext(fileX)  
        if ext in '.pdf': #이선호 연구원 
            pass
            #with PDF(fileX) as pdf:
             #   pdf.parse_content()
              #  print(pdf.content)
        elif ext in '.hwp': 
            print('hwp')
        elif ext in ('.doc', 'xls', 'ppt'): 
            object = Compound(fileX) 
            object.parse()
            print('COMPOUND')
        elif ext in ('.docx', 'xlsx', 'pptx'): 
            #test2 = OOXML(fileX)
            #test2.parse_ooxml()
            print('OOXML')
        else:
            print('NONE')

def main():
    try:
        inPath = "C:\\Users\\kukheon\\Desktop\\test"
        inFileList = [f for f in listdir(inPath) if isfile(join(inPath, f))]
        iitp3_manager = IITP3()
    
        for extChk in inFileList:
            iitp3_manager.ModuleSelect(extChk)

    except KeyboardInterrupt:
        print('error')

if __name__ == "__main__":
    main()
