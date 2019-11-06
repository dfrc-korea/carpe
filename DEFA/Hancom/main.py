# -*- coding:utf-8 -*-
import sys
from carpe_hwp import HWP
import os

def main(DirectoryPath):
            hwp_test = HWP(DirectoryPath)
            hwp_test.parse()

            
            print("파일명 : " + hwp_test.fileName)
            print("파일크기 : ", hwp_test.fileSize, "Bytes")
            print("파일타입 : " + hwp_test.fileType)

            print("\n")
            if (hwp_test.isDamaged):
                print("파일 손상 여부 : O")
            else:
                print("파일 손상 여부 : X")

            if (hwp_test.isEncrypted):
                print("파일 암호화 여부 : O")
            else:
                print("파일 암호화 여부 : X")

            print("\n")
            print("문서 메타데이터 출력")

            if (hwp_test.has_metadata):
                for meta in hwp_test.metaList:
                    print("Title : " + meta['title'])
                    print("Subject : " + meta['subject'])
                    print("Author : " + meta['author'])
                    print("Keyword : " + meta['keyword'])
                    print("Explanation : " + meta['explanation'])
                    print("LastSavedBy : " + meta['lastSavedBy'])
                    print("Version : " + meta['version'])
                    print("LastPrintedTime : " + meta['lastPrintedTime'])
                    print("CreateTime : " + meta['createTime'])
                    print("LastSavedTime : " + meta['lastSavedTime'])
                    print('Date : ' + meta['date'])
                    print("\n")
            else:
                print("문서 메타데이터 데이터 없음")

            print("\n")
            if (hwp_test.isCompressed):
                print("본문 압축 여부 : O")
            else:
                print("본문 압축 여부 : X")

            if (hwp_test.has_content):
                print("본문 : " + hwp_test.content)
            else:
                print("본문 데이터 없음")
                os.system('Pause')
            
if __name__ == "__main__":
    main(sys.argv[1])