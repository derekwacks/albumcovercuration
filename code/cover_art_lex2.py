import json
import boto3
from boto3.dynamodb.conditions import Key
import random
from time import sleep
import os


access_key_id = os.environ['access_key_id']
secret_access_key = os.environ['secret_access_key']


s3 = boto3.client('s3', aws_access_key_id=access_key_id,
                  aws_secret_access_key=secret_access_key,
                  region_name="us-west-2")
                  
                  

lambda_client = boto3.client('lambda', aws_access_key_id=access_key_id,
                  aws_secret_access_key=secret_access_key,
                  region_name="us-west-2")
      
                  
# Setting up SQS
sqs = boto3.resource('sqs', aws_access_key_id=access_key_id,
                     aws_secret_access_key=secret_access_key, region_name='us-west-2')
# Get the queue. This returns an SQS.Queue instance
queue_name = "music_rec_queue1"
queue = sqs.get_queue_by_name(QueueName=queue_name)
print(queue.url)                  
    
    
def get_user_data_from_table(lexid):
    dynamodb = boto3.resource('dynamodb', aws_access_key_id=access_key_id,
                            aws_secret_access_key=secret_access_key,
                            region_name="us-west-2")
    table = dynamodb.Table("Curation-2asrsupzz5auhprcbtbpba72ze-dev")
    response = table.query(
        KeyConditionExpression=Key('id').eq(lexid)
    )
    print(response)
    return response
    
    
def send_to_queue(data_as_list):
    # Trigger lambda and pass animal, fav color, genre, LEXID to new lambda (don't wait for response) 
    # query database with LEXID
    lexid = data_as_list[0]
    animal = data_as_list[1]
    fav_color = data_as_list[2]
    genre = data_as_list[3]
    """
    # Get user data from dynamoDB table
    TABLE_NAME = "Curation-66get7pmenf3vjacu2xats23xa-dev"
    resp = dynamodb.get_item(
    TableName=TABLE_NAME,
    Key={
        'id': {
            'S': lexid
        }
    })
    if "Item" in resp.keys():
        username = resp['Item']['username']
        user_email = resp['Item']['email']
    """
    sleep(1)
    resp = get_user_data_from_table(lexid)
    
    if "Items" in resp.keys():
        username = resp['Items'][0]['user']
        user_email = resp['Items'][0]['name']
    
    print("User info:", username, user_email)
    
    # Sending to queue 1
    mbody = "Client recommendation request" + str(random.random())
    attr = {
        'animal': {
            'DataType': 'String',
            'StringValue': str(animal)
        },
        'fav_color': {
            'DataType': 'String',
            'StringValue': str(fav_color)
        },
        'genre': {
            'DataType': 'String',
            'StringValue': str(genre)
        },
        'username': {
            'DataType': 'String',
            'StringValue': str(username)
        },
        'user_email': {
            'DataType': 'String',
            'StringValue': str(user_email)
        }
    }  
    
    
    # SENDING MESSAGE TO SQS
    response = queue.send_message(MessageBody=mbody, MessageAttributes=attr)
    print(response.get('MessageId'))
    return response



def lambda_handler(event, context):
    print(event)
    data = event['data'] # string of lexid, animal, color, genre separated by " "
    data_as_list = data.split(" ")
    print("Data", data_as_list)
    
    resp = send_to_queue(data_as_list)
    print(resp)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }


