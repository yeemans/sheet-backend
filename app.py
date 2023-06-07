from flask import Flask
from flask import request
from flask_cors import CORS
from pymongo import MongoClient
from bson.json_util import dumps
import json
from werkzeug.security import generate_password_hash, check_password_hash

client = MongoClient('mongodb://localhost:27017/')
db = client.local

app = Flask(__name__)
CORS(app)

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
        return dumps({"message": "success"})

    except Exception as e: 
        print(e)
        return dumps({f'message: {e}'})
