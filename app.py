from flask import Flask
from flask import request
from flask_cors import CORS
from pymongo import MongoClient
from bson.json_util import dumps
import json
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
import io
from os import environ
import boto3, botocore

client = MongoClient('mongodb://localhost:27017/')
db = client.local

app = Flask(__name__)
CORS(app)
app.config['S3_BUCKET'] = environ.get("S3_BUCKET")
app.config['S3_KEY'] = environ.get("S3_KEY")
app.config['S3_SECRET'] = environ.get("S3_SECRET")
app.config['S3_LOCATION'] = 'http://{}.s3.amazonaws.com/'.format(environ.get("S3_BUCKET"))

s3 = boto3.client(
   "s3",
   aws_access_key_id=app.config['S3_KEY'],
   aws_secret_access_key=app.config['S3_SECRET']
)

@app.route("/", methods=['GET'])
def home():
    return dumps({"llo"}) # testing

@app.route("/sign-up", methods = ['POST'])
def sign_up():
    try:
        data = json.loads(request.data)
        user_name = data['username']
        password = data['password']

        if user_name and password:

            status = db.Accounts.insert_one({
                "name": user_name,
                "password": generate_password_hash(password)
            })

            print(f"pass: #{password}")
            print(status.acknowledged)
            return dumps({'message' : "success"})
    except Exception as e:
        print(e)
        return dumps({'message': 'error'})


@app.route("/login", methods=["POST"])
def login(): 
    try: 
        data = json.loads(request.data)
        user = db.Accounts.find_one({"name": data['username']})
        print(user)
        if not check_password_hash(user["password"], data["password"]): 
            return dumps({"message": "User not found."})
    
        session_id = generate_password_hash("secretPassword101")
        status = db.Sessions.insert_one({ 
            "user": user["name"], 
            "session_id": session_id
        })

        print(status.acknowledged)
        print(session_id)
        return dumps({"message": "success", "session": session_id})

    except Exception as e: 
        print(e)
        return dumps({'message': {e}})

@app.route("/is-logged-in", methods=["POST"])
def is_logged_in(): 
    try:
        data = json.loads(request.data)
        session = db.Sessions.find_one({"session_id": data["sessionId"]})

        if session: 
            return dumps({"message": "success", "user": session["user"]})
        return dumps({"message": "User is not logged in."})
    
    except Exception as e: 
        print(e)
        return dumps({'message': {e}})
    
@app.route("/upload-sheet", methods=["POST"])
def upload_sheet(): 
    try:
        print(request.files["sheet"])
        sheet = request.files["sheet"]
        if not sheet: return dumps({"message": "empty file"})


        file_url = upload_file_to_s3(sheet, app.config["S3_BUCKET"])
        status = db.Sheets.insert_one({"sheet": file_url})
        print(status.acknowledged)
       

        return dumps({"message": "success", "sheet": file_url})
    except Exception as e: 
        print(e)
        return dumps({"message": e})

def upload_file_to_s3(file, bucket_name, acl="public-read"):
    try:
        s3.upload_fileobj(
            file,
            bucket_name,
            file.filename,
            ExtraArgs={
                "ACL": acl,
                "ContentType": file.content_type    #Set appropriate content type as per the file
            }
        )
    except Exception as e:
        print("Something Happened: ", e)
        return e
    return "{}{}".format(app.config["S3_LOCATION"], file.filename)