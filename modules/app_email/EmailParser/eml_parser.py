import email

def main(self):
    if __debug__: 
        import os
        assert os.path.isdir(self.exportDir)
    #msg = email.message_from_file(open(self.fileName))
    # https://stackoverflow.com/questions/16343248/how-to-handle-python-3-x-unicodedecodeerror-in-email-package
    msg = email.message_from_binary_file(open(self.fileName, 'rb'))
    msg_info = self.parseEML(1, 1, msg)
    #self.makeMessageFile(1, 1, msg_info)
    return msg_info
"""
if __name__ == "__main__": 
    pass
else:
    from modules.app_email.EmailBoxClass import EmailBox
    EmailBox.main = main
"""