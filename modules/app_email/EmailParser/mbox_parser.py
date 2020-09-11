import mailbox

def main(self):
    if __debug__: 
        import os
        assert os.path.isdir(self.exportDir)

    mbox = mailbox.mbox(self.fileName)
    #print(len(mbox))
    msg_no = 1
    result = list()
    for msg in mbox:
        msg_info = self.parseEML(1, msg_no, msg)
        result.append(msg_info)
        #self.makeMessageFile(1, msg_no, msg_info)
        msg_no += 1
    return result

"""
if __name__ == "__main__": 
    pass
else:
    from modules.app_email.EmailBoxClass import EmailBox
    EmailBox.main = main
"""
