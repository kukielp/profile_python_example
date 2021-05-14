import os, uuid, requests, hashlib, random
from PIL import Image,ImageFilter
import wave, struct

import threading
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Key

from flask import Flask, request, jsonify
from flask_lambda import FlaskLambda

EXEC_ENV = os.environ['EXEC_ENV']
REGION = os.environ['REGION_NAME']
TABLE_NAME = os.environ['TABLE_NAME']
SQS_API_URL = os.environ['SQS_API_URL']


if EXEC_ENV == 'local':
    app = Flask(__name__)
    #dynamodb = boto3.resource('dynamodb', endpoint_url='http://dynamodb:8000')
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
else:
    app = FlaskLambda(__name__)
    dynamodb = boto3.resource('dynamodb', region_name=REGION)


def db_table(table_name=TABLE_NAME):
    return dynamodb.Table(table_name)


def parse_user_id(req):
    '''When frontend is built and integrated with an AWS Cognito
       this will parse and decode token to get user identification'''
    print(req.headers)
    return req.headers['Authorization'].split()[1]

def resize_n_upload(original_file, New_file, date_time, s3_key_name):
    s3_client = boto3.client('s3')
    s3_bucket_name = "image-bucket-paul"

    im = Image.open(original_file)

    if New_file == '/tmp/thumb_electricals.jpeg':
        im = im.filter(filter=ImageFilter.BLUR)
        im = im.transpose(Image.ROTATE_90)
        size = (480, 640)
        im.thumbnail(size) 
    else:
        size = (1024, 768)
        im.thumbnail(size) 
    
    im.save(New_file)

    s3_client.upload_file(New_file, s3_bucket_name, s3_key_name)

@app.route('/lists')
def fetch_lists():
    try:
        user_id = parse_user_id(request)
    except:
        return jsonify('Unauthorized'), 401

    if random.uniform(0, 100) > 50 :
        now = datetime.now() # current date and tim
        date_time = now.strftime("%m_%d_%Y__%H_%M_%S")
        print("date and time:",date_time)	
        
        processes = list()

        s3_key_name = 'images/' + date_time + '.jpg'
        p1 = threading.Thread(target=resize_n_upload, args=('electricals.jpeg', '/tmp/smaller_electricals.jpeg', date_time, s3_key_name))
        processes.append(p1)
        p1.start()
        s3_key_name = 'images/thumb_' + date_time + '.jpg'
        p2 = threading.Thread(target=resize_n_upload, args=('electricals.jpeg', '/tmp/thumb_electricals.jpeg', date_time, s3_key_name))
        processes.append(p2)
        p2.start()
        
        for process in processes:
            process.join()

    tbl_response = db_table().query(KeyConditionExpression=Key('userId').eq(user_id))
    for item in tbl_response['Items']:
        response = requests.get("https://" + SQS_API_URL + "/Prod/json.cfm?listid=" + item['listId'])
    return jsonify(tbl_response['Items'])


@app.route('/lists', methods=('POST',))
def create_list():
    list_id = str(uuid.uuid4())
    try:
        user_id = parse_user_id(request)
    except:
        return jsonify('Unauthorized'), 401

    list_data = request.get_json()
    list_data.update(userId=user_id, listId=list_id)
    tbl = db_table()
    tbl.put_item(Item=list_data)
    tbl_response = tbl.get_item(Key={'userId': user_id, 'listId': list_id})
    return jsonify(tbl_response['Item']), 201


@app.route('/lists/<string:list_id>')
def fetch_list(list_id):
    try:
        user_id = parse_user_id(request)
    except:
        return jsonify('Unauthorized'), 401

    tbl_response = db_table().get_item(Key={'userId': user_id, 'listId': list_id})
    return jsonify(tbl_response['Item'])


@app.route('/lists/<string:list_id>', methods=('PUT',))
def update_list(list_id):
    try:
        user_id = parse_user_id(request)
    except:
        return jsonify('Unauthorized'), 401

    list_data = {k: {'Value': v, 'Action': 'PUT'}
                for k, v in request.get_json().items()}
    tbl_response = db_table().update_item(Key={'userId': user_id, 'listId': list_id},
                                          AttributeUpdates=list_data)
    return jsonify()


@app.route('/lists/<string:list_id>', methods=('DELETE',))
def delete_list(list_id):
    try:
        user_id = parse_user_id(request)
    except:
        return jsonify('Unauthorized'), 401

    db_table().delete_item(Key={'userId': user_id, 'listId': list_id})
    return jsonify()

def fibonacci(index):
    """
    Recursive function that calculates Fibonacci sequence.
    :param index: the n-th element of Fibonacci sequence to calculate.
    :return: n-th element of Fibonacci sequence.
    """

    if index <= 1:
        return index
    return fibonacci(index - 1) + fibonacci(index - 2)


@app.route('/fib/<int:n>')
def fib(n):
    
    for _ in range(10):
         result = { 'The ' + str(n) + ' fibonacci number is' : fibonacci(n)}
    return jsonify(result)


@app.route('/wavefile')
def wave_api():

    if random.uniform(0, 100) > 65:
        wavefile = wave.open('ImperialMarch60.wav', 'r')

        length = wavefile.getnframes()
        for i in range(0, length):
            wavedata = wavefile.readframes(1)
            data = struct.unpack("<h", wavedata)
            print(int(data[0]))
    
        return jsonify({ 'fileName' : 'ImperialMarch60', 'done':True})
    return jsonify({ 'fileName' : 'ImperialMarch60', 'done':True})





@app.route('/check')
def check():
    try:
        user_id = parse_user_id(request)
    except:
        return jsonify('Unauthorized'), 401

    tbl_response = db_table().query(KeyConditionExpression=Key('userId').eq(user_id))

    
    result = []
    
    response = requests.get("https://" + SQS_API_URL + "/Prod/getafew.cfm")
    for remote_list in response.json():
        remote_list_id = remote_list['body'].split()[-1]
        found = False
        for dynamo_list in tbl_response['Items']:
            dynamo_list_id = dynamo_list['listId']
            if dynamo_list_id == remote_list_id:
                found = True
                hash = hashlib.md5(remote_list['body'].encode()).hexdigest()
                if hash == remote_list['md5']:
                    result.append( 
                        { 
                            'itemBody' : remote_list['body'], 
                            'verifiedMd5' : True,
                            'ourMd5' : hash,
                            'thierMd5' : remote_list['md5']
                        }
                    )
        if not found:
            result.append( 
                        { 
                            'itemBody' : remote_list['body'], 
                            'error' : True
                        }
                    )

    
    return jsonify(result)


if EXEC_ENV == 'local':
    if __name__ == "__main__":
        app.run()