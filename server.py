from fastapi import FastAPI,File , UploadFile,Form
from pydantic import BaseModel
from random import choice
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import os
import configparser
from graph import Graph

client = MongoClient('mongodb://localhost:27017/')

##############Graph API interface #############################################################
config = configparser.ConfigParser()
config.read(['config.cfg', 'config.dev.cfg'])
azure_settings = config['azure']
graph: Graph = Graph(azure_settings)
# For testing the working of the  graph api integration
def greet_user(graph: Graph):
    user = graph.get_user()
    print('Hello,', user['displayName'])
    # For Work/school accounts, email is in mail property
    # Personal accounts, email is in userPrincipalName
    print('Email:', user['mail'] or user['userPrincipalName'], '\n')
greet_user(graph)

##############################################################################################

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
    )
######################## Test API #############################################################
@app.get('/')
async def get():
    return True
######### API related to users #################################################################

class UserModel(BaseModel):
    name : str
    email : str
    password : str
    firstlogin : bool
    status : str = 'pending'

### create a new user and also create a folder with email as filename
@app.post('/user')
async def add_user(user: UserModel):
    filter = {
        'email': user.email,
    }
    if client.bgv.user.count_documents(filter) == 0:
        try:
            os.mkdir(user.email)
        except FileExistsError as e:
            print (str(e))
        try:
            client.bgv.user.insert_one(dict(user))
            return True
        except Exception as e:
            print('Error inserting user: %s' % e)
    else : 
        return False

#### getting user information from database

@app.get('/user')
async def get_user(email : str):
    filter = {
        'email': email
    }
    project = {
        '_id': 0,
    }
    if client.bgv.user.count_documents(filter) == 1:
        return dict(client.bgv.user.find_one(filter,project))
    else : 
        return False

#### generating otp for email verification
@app.get('/otp')
async def otp(email: str):
    number =['0','1','2','3','4','5','6','7','8','9']
    otp =''
    for i in range(6):
        otp+=choice(number)

    subject = "OTP for New Account Created"
    msg = f" Hi \n The OTP your email verification is {otp} in the verifychain application\n\n "
    graph.send_mail(subject,msg,email)
    return otp

####  comparing OTP with existing user account


@app.post('/emailverified')
async def checkotp(email : str ):

    filter = { 'email' : email}
    update = {
        '$set': {'emailverified' : True}
    }
    try:
        client.bgv.user.find_one_and_update(filter,update)
        return True
    except Exception as e:
        print ("Error in updating email verification status"+str(e))
        return False

## the personal data input api for the user     

class PersonalData(BaseModel):

    empid : str
    doj : str
    email : str
    company_mail : str
    mob : str
    aadhaar: str
    pan : str
    passport : str
    personal : bool = True

@app.post('/userupdate')
async def update( data : PersonalData ):
    filt = {
        'email' : data.email
    }
    update={
        '$set':{
        'empid': data.empid,
        'doj': data.doj,
        'company_mail': data.company_mail,
        'mob': data.mob,
        'aadhaar': data.aadhaar,
        'pan': data.pan,
        'passport': data.passport,
        'personal': data.personal,
        }
    }

    try: 
        client.bgv.user.find_one_and_update(filt, update)
        return True
    except Exception as e:
        print (str(e))
        return False
## sslc certificate input

class SSLC(BaseModel):
    regno : str
    email : str
    marks : int
    school : str
    passout : str
    name : str
    board : str
    status : bool = False

@app.post('/sslc')
async def sslcinput(sslc : SSLC):
    filter = {
        'regno': sslc.regno,
        'email': sslc.email,
    }
    if client.bgv.sslc.count_documents(filter) == 0:
        try:
            client.bgv.sslc.insert_one(dict(sslc))
            return True
        except Exception as e:
            print (str(e))
    else: return False

### code to upload pdf file 
@app.post('/uploadsslcpdf')
def upload(email : str = Form(), regno : str = Form(),file: UploadFile = File(...)):
    
    path = os.path.join(email,regno+".pdf")
    try:
        contents = file.file.read()
        with open(path, 'wb') as f:
            f.write(contents)
    except Exception:
        return False
    finally:
        file.file.close()

    return True

## hser certificate input

class HSE (BaseModel):
    regno: str
    email : str
    name : str
    marks : int
    passout : str
    school : str
    board : str
    status : bool = False

@app.post('/hse')
async def hseinput(hse : HSE):
    filter = {
        'email': hse.email,
        'regno': hse.regno,
    }
    if client.bgv.hse.count_documents(filter) == 0:
        try:
            client.bgv.hse.insert_one(dict(hse))
            return True
        except Exception as e:
            print (str(e))
    else: 
        return False

@app.post('/uploadhsepdf')
def upload(email : str = Form(), regno : str = Form(),file: UploadFile = File(...)):
    
    path = os.path.join(email,regno+".pdf")
    try:
        contents = file.file.read()
        with open(path, 'wb') as f:
            f.write(contents)
    except Exception:
        return False
    finally:
        file.file.close()
    return True

# --------------- API for uploading UG data --------------------------------

class UG(BaseModel):
    regno : str
    email : str
    name : str
    specialization : str
    college : str
    marks : int
    passout : str
    university : str
    status : bool = False

@app.post('/ug')
async def addug(ug: UG):
    filter= {
        'email': ug.email,
        'regno': ug.regno,
    }
    if client.bgv.ug.count_documents(filter) == 0:
        try:
            client.bgv.ug.insert_one(dict(ug))
            return True
        except Exception as e:
            print(str(e))
    else: return False

@app.post('/uploadugpdf')
def upload(email : str = Form(), regno : str = Form(),file: UploadFile = File(...)):
    
    path = os.path.join(email,regno+".pdf")
    try:
        contents = file.file.read()
        with open(path, 'wb') as f:
            f.write(contents)
    except Exception:
        return False
    finally:
        file.file.close()
    return True

class Experience(BaseModel):
    empid : str
    name : str
    email : str
    company : str
    hr_mail : str
    start_date : str
    end_date : str
    designation : str
    lpa : str
    reporting_manager : str
    status : bool = False
######### Experience models and API ################################

@app.post('/exp')
async def add_exp(exp :Experience):
    filter = {
        'email': exp.email,
        'empid': exp.empid,
    }
    if client.bgv.exp.count_documents(filter) == 0: 
        try :
             client.bgv.exp.insert_one(dict(exp))
             return True
        except Exception as e:
            print(str(e))
    else : return False


@app.post('/uploadexppdf')
def upload(email : str = Form(), empid : str = Form(),file: UploadFile = File(...)):
    
    path = os.path.join(email,empid+".pdf")
    try:
        contents = file.file.read()
        with open(path, 'wb') as f:
            f.write(contents)
    except Exception:
        return False
    finally:
        file.file.close()
    return True

@app.get('/exp')
async def exp(empid : str ):
    filter= {
        "empid" : empid
    }
    project={
        "_id":0
    }
    return dict(client.bgv.exp.find_one(filter,project))
 
        
################################################################################################

############### API related to HR ##############################################################

class HrModel(BaseModel):
    name : str
    empid :str
    company_email : str
    password : str
    firstlogin: bool

@app.post('/hr')
async def add_hr(hr:HrModel):
    filter = {
        'company_email': hr.company_email
    }
    if client.bgv.hr.count_documents(filter) == 0:
        try:
            client.bgv.hr.insert_one(dict(hr))
            return True
        except Exception as e:
            print('Error inserting hr'+ str(e))
            return False
    else: 
        return False
################################################################################################

############### API related to Notary ##########################################################
class NotaryModel(BaseModel):
    name : str
    email : str
    aadhaar :str
    password : str
    firstlogin : bool

@app.post('/notary')
async def add_notary(notary:NotaryModel):
    filter = {
        'email': notary.email,
    }
    if client.bgv.notary.count_documents(filter) == 0:
        try:
            client.bgv.notary.insert_one(dict(notary))
            return True
        except Exception as e:
            print ('Error inserting notary'+ str(e))
    else :
        return False

#################################################################################################

##################################### Login API #################################################
class Login(BaseModel):
    email :str
    password : str

@app.post("/login")
async def login(login : Login):
    filter = dict(login)

    if client.bgv.user.count_documents(filter) ==1:
        return {'status': True,'user': 'user'}
    else:
        if client.bgv.notary.count_documents(filter) ==1:
                return {'status':True, 'user' : 'notary'}
        else:
            filter = {
                'company_email' : login.email,
                'password' : login.password
            }
            if client.bgv.hr.count_documents(filter) ==1:
                return {'status' : True, 'user': 'hr'}
            else :
                return {'status': False, 'user' : 'Check login creadentials'}
            
@app.get('/inbox')
async def inbox():
    inbox=graph.get_inbox()
    newmail=[]
    for i in range(len(inbox['value'])):
        if ('RE' not in inbox['value'][i]['subject']):
            if ('FW' not in inbox['value'][i]['subject']):
                if ('Re' not in inbox['value'][i]['subject']):
                        newmail.append(inbox['value'][i])
    maildata=[]
    for i in range(len(newmail)):
        if (client.bgv.email.count_documents({'id': newmail[i]['id']})==0):
            maildata.append(newmail[i])
    return maildata

@app.get('/pendingexp')
async def pendingexp():
    filter ={
        'status': False
    }
    project={
        '_id':0
    }
    try:
        return list(client.bgv.exp.find(filter, project))
    except Exception as e:
        print (str(e))
        return False
class Sendprofile(BaseModel):
    id : str
    email : str
    status : str= "replied"

@app.post('/sendprofile')
async def sendprofile(profile: Sendprofile):
    try:
        subject = "Employement Verification Link"
        link = "http://localhost:3000/expsearch"
        msg = f" Hi \n This is a system generated mail generated against your enquiry for employement verification in our company.\n Please click on the following link  and follow instructions to see the employement details\n\n {link}\n\n "
        graph.send_mail(subject,msg,profile.email)
        client.bgv.email.insert_one(dict(profile))
        return True
    except Exception as e:
        print (str(e))
        return False
    
class Deletemail(BaseModel):
    id : str
    email : str
    status : str= "deleted"

@app.post('/deletemail')
async def deletemail(delete : Deletemail):
    try :
        client.bgv.email.insert_one(dict(delete))
        return True
    except Exception as e:
        print(str(e))
        return False

class Email(BaseModel):
    empid : str
    status : str= "emailed"

@app.post('/verifydatamail')
async def verifydatamail(empdata : Email):
    filter={
    'empid': empdata.empid
    }
    project={
        '_id': 0, 
        'name': 1, 
        'hr_mail': 1
    }
    try : 
        expdetails=dict(client.bgv.exp.find_one(filter,project))
    except Exception as e:
        print(str(e))

    try :
        subject = f" Employment Verification of {expdetails['name']} with Employee ID { empdata.empid}"
        link = f"http://localhost:3000/approveexp"
        msg = f" Hi \n This is a system generated mail to initiate the employment verification of { expdetails['name']} with employee ID { empdata.empid }. \n\n Please use the following link to complete the same \n\n {link} \n\n Please refrain from sending further messages to this mail and use the link to complete the verification \n\n"
        graph.send_mail(subject,msg,expdetails['hr_mail'])
        update= {
            '$set': {'status': empdata.status }
        }
        try :
            client.bgv.exp.find_one_and_update(filter,update)
            return True
        except Exception as e :
            print( str(e))    
    except Exception as e: 
            print(str(e)) 
            return False

@app.post('/expstatusupdate')
async def statusupdate( expdata: Email):
    filter = {
         'empid': expdata.empid
    }
    update ={
        '$set': {'status': expdata.status}
    }
    try : 
        client.bgv.exp.find_one_and_update(filter,update)
        return True
    except Exception as e : 
        print( str(e))
        return False