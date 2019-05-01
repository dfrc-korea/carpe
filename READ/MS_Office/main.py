import unittest
from carpe_compound import Compound
import sys


def main(filePath):
    """
    with MariaDB(user='root', password='toor') as maria:
        maria.query("CREATE DATABASE carpe_vegetable")
    """

    object = Compound(filePath)

    if object.fp == None:
        return

    """
    ### Test Code ###
    print("fileSize : " + str(object.fileSize))
    print("fileName : " + str(object.fileName))
    print("fileType : " + str(object.fileType))
    print("filePath : " + str(object.filePath))
    print("isDamaged : ")
    if object.is_damaged == object.CONST_DOCUMENT_NORMAL:
        print("Normal")
    if object.is_damaged == object.CONST_DOCUMENT_DAMAGED:
        print("Damaged")
    """

    object.parse()

    object.fp.close()

if __name__ == "__main__":
    main(sys.argv[1])