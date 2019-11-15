import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from Carpe_OOXML import OOXML

if __name__ == '__main__':
    # 정상 / 비정상
    #horensic = OOXML("./normal.docx")
    #horensic = OOXML("./damaged.docx")
    #horensic = OOXML("./normal.xlsx")
    #horensic = OOXML("./damaged.xlsx")
    #horensic = OOXML("./normal.pptx")
    #horensic = OOXML("./damaged.pptx")

    # 비정상 + 옵션
    #horensic = OOXML("./damaged_contentdeleted.docx")
    #horensic = OOXML("./damaged_metadatadeleted.docx")


    # 5 samples
    # docx
    #horensic = OOXML("./6_2018_05_04!08_12_58_PM.docx")
    #horensic = OOXML("./300_quiz6_answer.docx")
    #horensic = OOXML("./[01-2]_타임라인 포렌식 분석 기초 테스트.docx")
    #horensic = OOXML("./Computer-Forensics-Training-Manual.docx")
    #horensic = OOXML("./Digital Forensics.docx")

    #pptx

    #horensic = OOXML("./BNY_Digital_Evidence.pptx")
    #horensic = OOXML("./Digital Forensics Case Brief.pptx")
    #horensic = OOXML("./Digital Forensics COSC 380 Spring 2013.pptx")
    #horensic = OOXML("./unit_ii_foundations_of_digital_forensics.pptx")
    #horensic = OOXML("./디지털포렌식의 동향과 전문인력양성방안_김용호.pptx")

    #xlsx

    #horensic = OOXML("./(붙임4)2017학년도1학기연계전공수업시간표.xlsx")
    #horensic = OOXML("./2018-19 DIG FORENSICS Minor Advising Sheet.xlsx")
    #horensic = OOXML("./Aventis-Class-Schedules-Official.xlsx")
    #horensic = OOXML("./FINAL-29Jul16-Career-Pathways-Matrix.xlsx")
    #horensic = OOXML("./List of case information Digital Forensics_tcm39-82992.xlsx")

    #test 190308



    #horensic = OOXML("./deleted_bottom.docx")
    #horensic = OOXML("./deleted_top.docx")

    #horensic = OOXML(".deleted_bottom.pptx")
    #horensic = OOXML("./deleted_top.pptx")

    #horensic = OOXML("./deleted_bottom.xlsx")
    #horensic = OOXML("./deleted_top.xlsx")

    #horensic = OOXML("./normal_xlsx.xlsx")
    #horensic = OOXML("./normal_pptx.pptx")
    #horensic = OOXML("./normal_docx.docx")

    #horensic = OOXML("./damaged_little.docx")

    horensic = OOXML(sys.argv[1])
    #horensic = OOXML("C:/Users/max/Downloads/temp/OOXML_Damaged/xlsx/(붙임4)2017학년도1학기연계전공수업시간표.xlsx")
    #horensic = OOXML("C:/Users/max/Downloads/temp/OOXML_Damaged/pptx/BNY_Digital_Evidence.pptx")
    #horensic = OOXML("C:/Users/max/Downloads/temp/OOXML_Damaged/xlsx/2018-19 DIG FORENSICS Minor Advising Sheet.xlsx")

    horensic.parse_ooxml()
