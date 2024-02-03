import os
import zipfile
import pandas as pd
import numpy as np
import re

import matplotlib.pyplot as plt
from keras.utils import to_categorical
import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
from keras.layers import Dense, Embedding, LSTM, SpatialDropout1D
from keras.models import Sequential
from keras_preprocessing.sequence import pad_sequences
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score, mean_squared_error, confusion_matrix
import seaborn as sns
import pickle

# Usage
# --------------------------------------------------------------------------
# df_MS = extractContents("dirPath")
# df_MS = allocLabel(df_MS, 'MS_label')
# df_MS = preProcessor(df_MS, output_path)
# --------------------------------------------------------------------------

def save_tokenizer(tokenizer, filename):
    """
    Save the tokenizer to a file.
    """
    with open(filename, 'wb') as handle:
        pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)

def load_tokenizer(filename):
    """
    파일에서 토크나이저의 상태를 불러와 새로운 Tokenizer에 적용합니다.
    """
    with open(filename, 'rb') as handle:
        tokenizer = pickle.load(handle)
        
    return tokenizer

def makeSequence(data, tokenizer=None, extension=None):
    # testing
    pk_path = extension + "_tokenizer_state.pickle"
    if tokenizer is not None:
        tokenizer.fit_on_texts(data['contents'].values)
        vocabSize = len(tokenizer.word_index) + 1    
        sequences = tokenizer.texts_to_sequences(data['contents'].values)
        ret_sequences = pad_sequences(sequences, maxlen=30)

        # 훈련 데이터에 대한 Tokenizer의 상태 저장
        save_tokenizer(tokenizer, pk_path)

    else:
        # 테스트 데이터에 대한 Tokenizer의 상태 불러오기
        loaded_tokenizer = load_tokenizer(pk_path)
        sequences = loaded_tokenizer.texts_to_sequences(data['contents'].values)
        
        ret_sequences = pad_sequences(sequences, maxlen=30)

        vocabSize = len(loaded_tokenizer.word_index) + 1

    return ret_sequences, vocabSize

def onehotencoder_fix(df, uniqueLabel):
    for label in uniqueLabel:
        df.loc[df['Label'] == label, 'Label'] = uniqueLabel.index(label)
    labels = to_categorical(df['Label'], len(uniqueLabel))

    return labels

def decode_onehot(labels, uniqueLabel):
    decoded_labels = list()
    
    for label in labels:
        index = np.argmax(label)
        decoded_labels.append(uniqueLabel[index])
    
    return decoded_labels

def getDataset(path):
    df = pd.read_csv(path, encoding='utf-8')

    return df

# learning model
def LSTM_Network(vocab_size=0, num_of_class=0, pad_sequences=None):
    
    model = Sequential()
    model.add(Embedding(vocab_size, 128, input_length=pad_sequences.shape[1]))
    model.add(SpatialDropout1D(0.2))
    model.add(LSTM(30, dropout=0.2, recurrent_dropout=0.2))
    model.add(Dense(num_of_class, activation='softmax')) # Dense(number of label, activation function)
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    
    return model

# Contents PKZIP elements name
def extractContents(dirPath):
    # Dataset 경로 + program_name
    input_path_docx = dirPath
    
    data = []

    for (root, dirs, files) in os.walk(input_path_docx):
        for zip in files:
            zip_path = root + os.sep + zip
            with zipfile.ZipFile(zip_path, 'r') as fp:
                # extract entry path
                info_list = []
                for info in fp.infolist():
                    info_list.append(info.filename)
                data.append([zip_path, info_list])

    df = pd.DataFrame(data, columns=['filename', 'contents'])
    
    return df

# StringToList define
def stringToList(string):
    listRes = list(string.split(", "))
    return listRes

# 따옴표 제거 등 문자열 전처리 함수
def removeChar(string):
    character = "'\"[],"

    ret = string.replace(character[0], "")
    ret = ret.replace(character[1], "")
    ret = ret.replace(character[2], "")
    ret = ret.replace(character[3], "")
    ret = ret.replace(character[4], "")
    ret = ret.lower()
    # 숫자 제거
    order = r'[0-9]'
    ret = re.sub(order, '', ret)
    
    return ret

def preProcessor(df):
    token_list = []  # 토큰화된 요소를 담을 리스트

    # Tokenization 적용
    for contents in df['contents']:
        files = str(contents)
        files = removeChar(files)
        content_list = stringToList(files)
        token_list.append(list(set(content_list)))

    # 패딩을 적용하여 모든 시퀀스를 길이 30으로 맞추기
    token_list = [(['nan'] * (30 - len(tokens)) + tokens)[:30] for tokens in token_list]
    # print(type(token_list))
    # print(token_list)
    # DataFrame 업데이트
    df['contents'] = [str(tokens) for tokens in token_list]
    
    return df

def allocLabel(df, label_name):
    label_list = []
    for idx in range(len(df)):
        label_list.append(label_name)
        
    df.insert(2, "Label", label_list, True)
    return df


# for Metrics
def showPlot(history):
    s, axe = plt.subplots(2,1,constrained_layout=True)
    axe[0].plot(history['accuracy'], c= 'b')
    axe[0].plot(history['val_accuracy'], c='r')
    axe[0].set_title('Word Program')
    axe[0].set_ylabel('accuracy')
    axe[0].set_xlabel('epoch')
    axe[0].legend(['train_acc', 'val_acc'], loc='lower right')

    axe[1].plot(history['loss'], c='m')
    axe[1].plot(history['val_loss'], c='c')
    axe[1].set_ylabel('loss')
    axe[1].set_xlabel('epoch')
    axe[1].legend(['train_loss', 'val_loss'], loc = 'upper right')
    
    plt.show()

def f1_score(precision, recall):
    ret = 2*(precision * recall)/(precision+recall)
    return ret

def get_clf_eval(y_test, pred, uniqueLabel):
    accuracy = accuracy_score(y_test, pred)
    precision = precision_score(y_test, pred, average="macro")
    recall = recall_score(y_test, pred, average="macro")
    roc_auc = roc_auc_score(y_test, pred, average="macro")
    rmse = mean_squared_error(y_test, pred, squared=False)
    f1score = f1_score(precision, recall)
    
    ### --------------------- confusion matrix heatmap
    ax = plt.subplot()
    cm = confusion_matrix(np.asarray(y_test).argmax(axis=1), np.asarray(pred).argmax(axis=1))
    sns.heatmap(cm, annot=True, fmt='g', ax=ax, cmap="Blues");  #annot=True to annotate cells, ftm='g' to disable scientific notation

    # labels, title and ticks
    ax.set_xlabel('Predicted labels');ax.set_ylabel('True labels'); 
    # ax.set_title('Classification Confusion Matrix - Word program'); 
    ax.xaxis.set_ticklabels(uniqueLabel); ax.yaxis.set_ticklabels(uniqueLabel)
    plt.xticks(rotation=90)
    plt.yticks(rotation=0)
        
    print("Accuracy: {}".format(accuracy))
    print("Precision: {}".format(precision))
    print("Recall: {}".format(recall))
    print("F1-score: {}".format(f1score))
    print("Roc-auc: {}".format(roc_auc))
    print("RMSE: {}".format(rmse))

    plt.show()

# 분석 결과를 DB에 넣기 위해 하나의 데이터프레임에 합치는 함수 (수정 필요)
def concat_df(based, src_df, dep_df, labels, extension):
    rang = len(src_df)

    for idx in range(0, rang):
        dep_df = dep_df.append({
            "par_id": based[0],
            "case_id": based[1],
            "evd_id": based[2],
            "filename": os.path.basename(src_df["filename"][idx]),
            "extension": extension,
            "source": labels[idx]
        }, ignore_index=True)

    return dep_df