from sklearn.model_selection import train_test_split
from scikeras.wrappers import KerasClassifier

from keras.preprocessing.text import Tokenizer
import advanced_modules.last_saved_program_classifier.module as module
import advanced_modules.last_saved_program_classifier.utils as utils

class DocxAnalyzer:
    def __init__(self):
        self.uniqueLabel = ['MS', 'MS_Mac', 'Libre', 'Libre_Mac', 'Polaris', 'Hancom2022', 'WPSOffice', 'FreeOffice', 'OnlyOffice' , 'OfficeSuite', 'Wordpad', 'SmartWord', 'TextEditor', 'Google', 'NaverOffice']
        self.train_data = module.preProcessor(module.getDataset(utils.DOCX_DIR_PATH))
        self.labels = module.onehotencoder_fix(df=self.train_data, uniqueLabel=self.uniqueLabel)
        self.tokenizer = Tokenizer()
        self.train_sequences, self.vocabSize = module.makeSequence(self.train_data, self.tokenizer, "docx")
        self.docx_clf = None

    def train_docx_model(self):
        # Model create
        self.docx_clf = KerasClassifier(model=module.LSTM_Network(vocab_size=self.vocabSize, num_of_class=len(self.uniqueLabel), pad_sequences=self.train_sequences), loss='categorical_crossentropy', validation_split=0.2,  shuffle=True, epochs=10, batch_size=64, verbose=True)
        for idx in [0, 500, 1000]:
            print(self.train_data["contents"][idx])
            print(self.train_sequences[idx])
            print(self.labels[idx])
            label = module.decode_onehot(self.labels[idx], self.uniqueLabel)
            print(label)
        # split dataset
        x_train, x_test, y_train, y_test = train_test_split(self.train_sequences, self.labels, test_size=0.2, random_state=7)
        # training
        self.docx_clf.fit(x_train, y_train)
        
        # testing = Testing
        module.showPlot(self.docx_clf.history)
        self.docx_clf.predict(x_test, y_test)
    
    def predict_document(self, data):
        target_seq = module.preProcessor(data)
        target_seq, vocabSize = module.makeSequence(target_seq, tokenizer=None, extension="docx")
        pred = self.docx_clf.predict(target_seq)
        return pred

class PptxAnalyzer:
    def __init__(self):
        self.uniqueLabel = ['MS', 'MS_Mac', 'Libre', 'Libre_Mac', 'Polaris', 'Hancom2022', 'WPSOffice', 'FreeOffice', 'OnlyOffice' , 'OfficeSuite', 'Google', 'NaverOffice']
        self.train_data = module.preProcessor(module.getDataset(utils.PPTX_DIR_PATH))
        self.labels = module.onehotencoder_fix(df=self.train_data, uniqueLabel=self.uniqueLabel)
        self.tokenizer = Tokenizer()
        self.train_sequences, self.vocabSize = module.makeSequence(self.train_data, self.tokenizer, "pptx")
        self.pptx_clf = None

    def train_pptx_model(self):
        # Model create
        self.pptx_clf = KerasClassifier(model=module.LSTM_Network(vocab_size=self.vocabSize, num_of_class=len(self.uniqueLabel), pad_sequences=self.train_sequences), loss='categorical_crossentropy', validation_split=0.2,  shuffle=True, epochs=10, batch_size=64, verbose=True)
        # split dataset
        x_train, x_test, y_train, y_test = train_test_split(self.train_sequences, self.labels, test_size=0.2, random_state=7)
        # training
        self.pptx_clf.fit(x_train, y_train)
        
        # testing = Testing
        module.showPlot(self.pptx_clf.history)
        self.pptx_clf.predict(x_test, y_test)
    
    def predict_document(self, data):
        target_seq = module.preProcessor(data)
        target_seq, vocabSize = module.makeSequence(target_seq, tokenizer=None, extension="pptx")
        pred = self.pptx_clf.predict(target_seq)
        return pred

class XlsxAnalyzer:
    def __init__(self):
        self.uniqueLabel = ['MS', 'MS_Mac', 'Libre', 'Libre_Mac', 'Polaris', 'Hancom2022', 'WPSOffice', 'FreeOffice', 'OnlyOffice' , 'OfficeSuite', 'Google', 'NaverOffice']
        self.train_data = module.preProcessor(module.getDataset(utils.XLSX_DIR_PATH))
        self.labels = module.onehotencoder_fix(df=self.train_data, uniqueLabel=self.uniqueLabel)
        self.tokenizer = Tokenizer()
        self.train_sequences, self.vocabSize = module.makeSequence(self.train_data, self.tokenizer, "xlsx")
        self.xlsx_clf = None

    def train_xlsx_model(self):
        # Model create
        self.xlsx_clf = KerasClassifier(model=module.LSTM_Network(vocab_size=self.vocabSize, num_of_class=len(self.uniqueLabel), pad_sequences=self.train_sequences), loss='categorical_crossentropy', validation_split=0.2,  shuffle=True, epochs=10, batch_size=64, verbose=True)
        # split dataset
        x_train, x_test, y_train, y_test = train_test_split(self.train_sequences, self.labels, test_size=0.2, random_state=7)
        # training
        self.xlsx_clf.fit(x_train, y_train)
        
        # testing = Testing
        module.showPlot(self.xlsx_clf.history)
        self.xlsx_clf.predict(x_test, y_test)
    
    def predict_document(self, data):
        target_seq = module.preProcessor(data)
        target_seq, vocabSize = module.makeSequence(target_seq, tokenizer=None, extension="xlsx")
        pred = self.xlsx_clf.predict(target_seq)
        return pred

# For testing
if __name__ == '__main__':
    
    # Create Analyzer
    docx_anl = DocxAnalyzer()
    pptx_anl = PptxAnalyzer()
    xlsx_anl = XlsxAnalyzer()

    # Train Analyzer
    docx_anl.train_docx_model()
    pptx_anl.train_pptx_model()
    xlsx_anl.train_xlsx_model()
