from .FiCALight import *


class FiCATool:
    def __init__(self, logout=None):
        self.flag = self.load_module(logout)

    def load_module(self, logout=None):
        self.fica = FiCA(out=logout)
        self.flag = self.fica.execute(FiCA.Instruction.LOAD_MODULE)

    def do_carve(self, _case_profile):
        self.fica.execute(FiCA.Instruction.NEW_CASE, _case_profile)
        _result = self.fica.execute(FiCA.Instruction.CARV)
        self.fica.execute(FiCA.Instruction.CLOSE_CASE)
        return _result

    def do_recarve(self, _case_profile):
        self.fica.execute(FiCA.Instruction.NEW_CASE, _case_profile)
        _result = self.fica.execute(FiCA.Instruction.RECARV)
        self.fica.execute(FiCA.Instruction.CLOSE_CASE)
        return _result

    def decode(self, _result):
        return self.fica.execute(FiCA.Instruction.DECODE, _result)


def main(case_profile):
    image_carver = FiCATool("carving.log")
    result = image_carver.do_carve(case_profile)
    copier = image_carver.decode(case_profile.get("out"))
    print(result)

    return copier
