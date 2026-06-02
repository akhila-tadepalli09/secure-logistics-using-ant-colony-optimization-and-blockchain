from django.shortcuts import render
from django.template import RequestContext
from django.contrib import messages
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
import os
from datetime import date
import json
from web3 import Web3, HTTPProvider
import ipfsApi
import pickle
from datetime import date
import pyaes, pbkdf2, binascii, os, secrets
import base64
import urllib, mimetypes
from django.http import HttpResponse
from string import punctuation
from nltk.corpus import stopwords
import nltk
from nltk.stem import WordNetLemmatizer
import pickle
from nltk.stem import PorterStemmer
import hashlib
from sklearn.feature_extraction.text import TfidfVectorizer #loading tfidf vector
from numpy import dot
from numpy.linalg import norm

global username, usersList, trapdoorList, contract, web3
stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()
ps = PorterStemmer()

api = ipfsApi.Client(host='http://127.0.0.1', port=5001)

#function to call contract
def getContract():
    global contract, web3
    blockchain_address = 'http://127.0.0.1:9545'
    web3 = Web3(HTTPProvider(blockchain_address))
    web3.eth.defaultAccount = web3.eth.accounts[0]
    compiled_contract_path = 'Logistic.json' #Logistic contract file
    deployed_contract_address = '0x2C97DD653aeaF299f38bF86d7db4b1C70c16A9fB' #contract address
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)  # load contract info as JSON
        contract_abi = contract_json['abi']  # fetch contract's abi - necessary to call its functions
    file.close()
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
getContract()

def getUsersList():
    global usersList, contract
    usersList = []
    count = contract.functions.getUserCount().call()
    for i in range(0, count):
        user = contract.functions.getUsername(i).call()
        password = contract.functions.getPassword(i).call()
        phone = contract.functions.getPhone(i).call()
        email = contract.functions.getEmail(i).call()
        address = contract.functions.getAddress(i).call()
        usersList.append([user, password, phone, email, address])

def getTrapdoor():
    global trapdoorList, contract
    trapdoorList = []
    count = contract.functions.getTrapCount().call()
    for i in range(0, count):
        uname = contract.functions.getOwner(i).call()
        fname = contract.functions.getFilename(i).call()
        trapdoor = contract.functions.getTrapdoor(i).call()
        dd = contract.functions.getDate(i).call()
        hc = contract.functions.getHashcode(i).call()
        trapdoorList.append([uname, fname, trapdoor, dd, hc])        

getUsersList()
getTrapdoor()

def index(request):
    if request.method == 'GET':
       return render(request, 'index.html', {})    

def Login(request):
    if request.method == 'GET':
       return render(request, 'Login.html', {})
    
def Register(request):
    if request.method == 'GET':
       return render(request, 'Register.html', {})

def Upload(request):
    if request.method == 'GET':
       return render(request, 'Upload.html', {})

def getKey(): #generating key with PBKDF2 for AES
    password = "s3cr3t*c0d3"
    passwordSalt = '76895'
    key = pbkdf2.PBKDF2(password, passwordSalt).read(32)
    return key

def encrypt(plaintext): #AES data encryption
    aes = pyaes.AESModeOfOperationCTR(getKey(), pyaes.Counter(31129547035000047302952433967654195398124239844566322884172163637846056248223))
    ciphertext = aes.encrypt(plaintext)
    return ciphertext

def decrypt(enc): #AES data decryption
    aes = pyaes.AESModeOfOperationCTR(getKey(), pyaes.Counter(31129547035000047302952433967654195398124239844566322884172163637846056248223))
    decrypted = aes.decrypt(enc)
    return decrypted

def calculateBlock(file_data):
    length = len(file_data)
    tot_blocks = 0
    size = 0
    if length >= 1000:
        size = length / 10
        tot_blocks = 10
    if length < 1000 and length > 500:
        size = length / 5
        tot_blocks = 5
    if length < 500 and length > 1:
        size = length / 3
        tot_blocks = 3
    return int(size), tot_blocks, length

#define function to clean text by removing stop words and other special symbols
def cleanText(doc):
    tokens = doc.split()
    table = str.maketrans('', '', punctuation)
    tokens = [w.translate(table) for w in tokens]
    tokens = [word for word in tokens if word.isalpha()]
    tokens = [w for w in tokens if not w in stop_words]
    tokens = [word for word in tokens if len(word) > 1]
    tokens = [ps.stem(token) for token in tokens]
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    tokens = ' '.join(tokens)
    return tokens

def getTrapdoor(filedata):
    data = filedata.decode()
    data = data.lower().strip()
    data = cleanText(data)
    data = data.split(" ")
    trapdoor = ""
    for i in range(len(data)):
        result = hashlib.md5(data[i].encode())
        trapdoor += result.hexdigest()+" "
    return trapdoor.strip()    

def UploadAction(request):
    if request.method == 'POST':
        global username
        today = date.today()   
        filedata = request.FILES['t1'].read()
        filename = request.FILES['t1'].name
        trapdoor = getTrapdoor(filedata)
        size, tot_blocks, length = calculateBlock(filedata)
        names = ""
        code = ""
        start = 0
        end = size
        block = []
        for i in range(0, tot_blocks):
            chunk = filedata[start:end]
            chunk = encrypt(chunk)
            block.append(chunk[0:20])
            start = end
            end = end + size
            chunk = pickle.dumps(chunk)
            hashcode = api.add_pyobj(chunk)
            names += filename+"_block_"+str(i)+" "
            code += hashcode+" "
        remain =  length - start
        if remain > 0:
            chunk = filedata[start:length]
            chunk = encrypt(chunk)
            block.append(chunk[0:20])
            start = start + remain
            chunk = pickle.dumps(chunk)
            hashcode = api.add_pyobj(chunk)
            names += filename+"_block_"+str(len(block))+" "
            code += hashcode+" "
        names = names.strip()
        code = code.strip()
        code_arr = code.split(" ")
        names_arr = names.split(" ")
        msg = contract.functions.saveTrapdoor(username, names, trapdoor, str(today), code).transact()
        tx_receipt = web3.eth.waitForTransactionReceipt(msg)
        trapdoorList.append([username, names, trapdoor, str(today), code])
        output = '<table border=1 align=center>'
        output+='<tr><th><font size=3 color=black>Uploader Name</font></th>'
        output+='<th><font size=3 color=black>Filename</font></th>'
        output+='<th><font size=3 color=black>Uploading Date</font></th>'
        output+='<th><font size=3 color=black>Chunk Name</font></th>'
        output+='<th><font size=3 color=black>Encrypted Chunk Data</font></th>'
        output+='<th><font size=3 color=black>Chunk Hashcode</font></th></tr>'
        for i in range(len(block)):
            output+='<tr><td><font size=3 color=black>'+username+'</font></td>'
            output+='<td><font size=3 color=black>'+filename+'</font></td>'
            output+='<td><font size=3 color=black>'+str(today)+'</font></td>'
            output+='<td><font size=3 color=black>'+names_arr[i]+'</font></td>'
            output+='<td><font size=3 color=black>'+str(block[i])+'</font></td>'
            output+='<td><font size=3 color=black>'+code_arr[i]+'</font></td></tr>'
        context= {'data': output}
        return render(request, 'UserScreen.html', context)
        
def DownloadAction(request):
    if request.method == 'GET':
        global username, trapdoorList
        filename = request.GET['file']
        arr = filename.split("_")
        if os.path.exists("SearchApp/static/"+arr[0]):
            os.remove("SearchApp/static/"+arr[0])
        for i in range(len(trapdoorList)):
            tl = trapdoorList[i]
            blocks = tl[1]
            bnames = blocks.split(" ")
            codes = tl[4].split(" ")
            for j in range(len(bnames)):
                bname = bnames[j].split("_")
                if bname[0] == arr[0]:
                    with open("SearchApp/static/"+arr[0], "ab") as myfile:
                        content = api.get_pyobj(codes[j])
                        content = pickle.loads(content)
                        content = decrypt(content)
                        myfile.write(content)                        
        myfile.close()
        with open("SearchApp/static/"+arr[0], "rb") as myfile:
            data = myfile.read()
        myfile.close()
        response = HttpResponse(data,content_type='application/force-download')
        response['Content-Disposition'] = 'attachment; filename='+arr[0]
        return response

def ACOSearch(request):
    if request.method == 'GET':
       return render(request, 'ACOSearch.html', {})

def runACO(vector, files, query_trap):
    result = []
    for i in range(len(vector)):
        aco_score = dot(vector[i], query_trap)/(norm(vector[i])*norm(query_trap))
        if aco_score > 0:
            file = files[i]
            file = file.split(" ")
            if file[0] not in result:
                result.append(file[0])
    return result

def getQueryTrapdoor(filedata):
    data = filedata.lower().strip()
    data = cleanText(data)
    data = data.split(" ")
    trapdoor = ""
    for i in range(len(data)):
        result = hashlib.md5(data[i].encode())
        trapdoor += result.hexdigest()+" "
    return trapdoor.strip()

def ACOSearchAction(request):
    if request.method == 'POST':
        global contract, userList, trapdoorList, username
        query = request.POST.get('t1', False)
        vector = []
        files = []
        for i in range(len(trapdoorList)):
            tl = trapdoorList[i]
            if tl[0] == username:
                vector.append(tl[2])
                files.append(tl[1])
        tfidf_vectorizer = TfidfVectorizer(stop_words=stop_words, use_idf=True, smooth_idf=False, norm=None, decode_error='replace', max_features=300)
        vector = tfidf_vectorizer.fit_transform(vector).toarray()
        print(vector)
        query_trap = getQueryTrapdoor(cleanText(query.lower().strip()))
        query_trap = tfidf_vectorizer.transform([query_trap]).toarray()
        aco_search = runACO(vector, files, query_trap[0])
        output = '<table border=1 align=center>'
        output+='<tr><th><font size=3 color=black>Uploader Name</font></th>'
        output+='<th><font size=3 color=black>Filename</font></th>'
        output+='<th><font size=3 color=black>Download File</font></th></tr>'
        for i in range(len(aco_search)):
            output+='<tr><td><font size=3 color=black>'+username+'</font></td>'
            output+='<td><font size=3 color=black>'+aco_search[i]+'</font></td>'
            output+='<td><a href=\'DownloadAction?file='+aco_search[i]+'\'><font size=3 color=black>Click Here</font></a></td></tr>'
        context= {'data': output}        
        return render(request, 'UserScreen.html', context)
            

def ViewBlocks(request):
    if request.method == 'GET':
        global username, trapdoorList
        output = '<table border=1 align=center>'
        output+='<tr><th><font size=3 color=black>Uploader Name</font></th>'
        output+='<th><font size=3 color=black>File Chunks</font></th>'
        output+='<th><font size=3 color=black>Trapdoor</font></th>'
        output+='<th><font size=3 color=black>Upload Date</font></th></tr>'
        for i in range(len(trapdoorList)):
            td = trapdoorList[i]
            if td[0] == username:
                output+='<tr><td><font size=3 color=black>'+td[0]+'</font></td>'
                output+='<td><font size=3 color=black>'+td[1]+'</font></td>'
                output+='<td><font size=3 color=black>'+td[2][0:100]+'</font></td>'
                output+='<td><font size=3 color=black>'+td[3]+'</font></td></tr>'
        context= {'data': output}        
        return render(request, 'UserScreen.html', context)     

def Signup(request):
    if request.method == 'POST':
        global contract, usersList
        username = request.POST.get('username', False)
        password = request.POST.get('password', False)
        contact = request.POST.get('contact', False)
        email = request.POST.get('email', False)
        address = request.POST.get('address', False)
        record = 'none'
        for i in range(len(usersList)):
            ul = usersList[i]
            if ul[0] == username:
                record = "exists"
                break
        if record == 'none':
            msg = contract.functions.saveUser(username, password, contact, email, address).transact()
            tx_receipt = web3.eth.waitForTransactionReceipt(msg)
            usersList.append([username, password, contact, email, address])
            context= {'data':'Signup process completed and record saved in Blockchain<br/>'+str(tx_receipt)}
            return render(request, 'Register.html', context)
        else:
            context= {'data':username+'Username already exists'}
            return render(request, 'Register.html', context)
        
def UserLogin(request):
    if request.method == 'POST':
        global username, usersList
        username = request.POST.get('username', False)
        password = request.POST.get('password', False)
        status = 'none'
        for i in range(len(usersList)):
            ul = usersList[i]
            if ul[0] == username and ul[1] == password:
                status = 'success'
                break
        if status == 'success':
            context= {'data':"Welcome "+username}
            return render(request, 'UserScreen.html', context)
        else:
            context= {'data':'Invalid login details'}
            return render(request, 'Login.html', context)            


        
        



        
            
