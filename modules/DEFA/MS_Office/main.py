import unittest
from carpe_compound import Compound
import sys, os


def main(filePath):
    
    filepath = sys.argv[1]
    for root, dirs, files in os.walk(filepath):
        for fname in files:
            full_fname = os.path.join(root, fname)
            print(full_fname)
            object = Compound(full_fname)
            if object.fp == None:
                return

            object.parse()
            # fp = open(".\\result\\" + fname[:-4] + ".txt", 'w', encoding='UTF-8')
            fp.write(object.content)
            fp.write(str(object.metadata['author']))
            fp.write(str(object.metadata['title']))
            object.fp.close()
    """
    object = Compound(filePath)
    if object.fp == None:
        return

    object.parse()
    print(object.content)
    object.fp.close()
    """


if __name__ == "__main__":
    main(sys.argv[1])