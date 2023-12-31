from flask import Flask,render_template,request
import cv2
from keras.models import load_model
import numpy as np
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.optimizers import Adam
from keras.layers import Dense, Flatten,Input, Convolution2D, Dropout, LSTM, TimeDistributed, Embedding, Bidirectional, Activation, RepeatVector,Concatenate
from keras.models import Model, Sequential
from keras.utils import np_utils
from keras.preprocessing import image,sequence
from keras.preprocessing.sequence import pad_sequences
from tqdm import tqdm
from flask import *
import pickle

resnet = load_model('resnet.h5')

print("loaded")


vocab = np.load("vocab.npy",allow_pickle=True)
vocab = vocab.item()
inv_vocab = {v:k for k,v in vocab.items()}

embedding_size = 128
max_len = 40
vocab_size = len(vocab)

image_model = Sequential()

image_model.add(Dense(embedding_size, input_shape=(2048,), activation='relu'))
image_model.add(RepeatVector(max_len))


language_model = Sequential()
language_model.add(Embedding(input_dim=vocab_size, output_dim=embedding_size, input_length=max_len))
language_model.add(LSTM(256, return_sequences=True))
language_model.add(TimeDistributed(Dense(embedding_size)))



conca = Concatenate()([image_model.output, language_model.output])
x = LSTM(128, return_sequences=True)(conca)
x = LSTM(512, return_sequences=False)(x)
x = Dense(vocab_size)(x)
out = Activation('softmax')(x)
model = Model(inputs=[image_model.input, language_model.input], outputs = out)
model.compile(loss='categorical_crossentropy', optimizer='RMSprop', metrics=['accuracy'])
model.load_weights('mine_model_weights.h5')
print("model loaded")



app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT']=1
 
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/after',methods=['GET','POST'])
def after():
    global model,vocab,inv_vocab,resnet
    file=request.files['file1']
    file.save('static/file.jpg')
    img=cv2.imread('static/file.jpg')
    img=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
    img=cv2.resize(img,(224,224))
    img=np.reshape(img,(1,224,224,3))
    features=resnet.predict(img).reshape(1,2048)
    text_in=['startofseq']
    final=''
    print("="*50)
    print("getting captions")
    
    count = 0
    while tqdm(count<20):
        count+=1
        encoded=[]
        for i in text_in:
            encoded.append(vocab[i])
        padded=pad_sequences([encoded],maxlen=max_len,padding='post',truncating='post')
        sampled_index=np.argmax(model.predict([features,padded]))
        sampled_word=inv_vocab[sampled_index]
        if sampled_word!= 'endofseq':
            final=final+' '+sampled_word
        text_in.append(sampled_word)
    return render_template('predict.html',final=final)
@app.route('/Home',methods=['GET','POST'])
def Home():
    return render_template("index.html")
@app.route('/login',methods=['POST'])
def login():
    return render_template('login.html')
@app.route('/About',methods=['POST'])
def About():
    return render_template("About.html")
@app.route('/error')  
def error():  
    return "<p><strong>Enter correct password</strong></p>"  
@app.route('/success',methods = ['POST','GET'])  
def success():  
    if request.method == "POST":  
        email = request.form['email']  
        password = request.form['pass']  
      
    if password=="gana":  
        resp = make_response(render_template('success.html')) 
        resp.set_cookie('email',email)  
        return resp  
        
    else:  
        return redirect(url_for('error'))  
@app.route('/viewprofile')  
def profile():  
    email = request.cookies.get('email')  
    l=list(email)
    k=l[:-10]
    st=""
    for i in k:
        st=st+i
    
    resp = make_response(render_template('index.html',name = st))  
    return resp  

if __name__ == "__main__":
    app.run(debug=True)