import json
import boto3
import math
import dateutil.parser
import datetime
import time
import os
import logging
import random
from botocore.config import Config
import matplotlib.colors as colors
from colorthief import ColorThief
from urllib.request import urlopen
import io
import ssl
import requests

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
access_key_id = os.environ['aws_access_key_id']
secret_access_key = os.environ['secretkey']
unsplash_access_key = os.environ['unsplash_access_key']
my_config = Config(
    region_name='us-west-2',
    signature_version='v4',
    retries={
        'max_attempts': 10,
        'mode': 'standard'
    }
)

# Setting up SQS
sqs = boto3.resource('sqs', aws_access_key_id=access_key_id,
                     aws_secret_access_key=secret_access_key, region_name='us-west-2')                  
# Get the queue. This returns an SQS.Queue instance
queue_name = "music_rec_queue2"
queue = sqs.get_queue_by_name(QueueName=queue_name)
print(queue.url)


def get_colors(image):
    """
    :param image: image to be analyzed
    :param fav_color: favorite color
    :return: palette[0] top color from image
    """
    # Gets most prominent color in the image
    color_count = 5
    color_thief = ColorThief(image)
    palette = color_thief.get_palette(color_count=color_count)
    print("palette:", palette)
    # return palette[0:3] returns top 3 colors
    return palette[0]  # return top color ex: (255, 255, 255)


def animal(a):
    # Get an example image
    a_key = "?client_id="+unsplash_access_key
    query_url = 'https://api.unsplash.com/search/photos/'+a_key+'&query='+a+'&per_page=1'
    r = requests.get(query_url)
    r = r.json()
    print(r)
    ret_url = r["results"][0]["urls"]["regular"]  # url of first pic of returned results
    print("ret", ret_url)
    context = ssl._create_unverified_context()
    fd = urlopen(str(ret_url), context=context)
    f = io.BytesIO(fd.read())
    col = get_colors(f)  # Get top color in pic
    return list(col)


def create_vector(animal_ani, fav_color):
    col_1 = colors.to_rgb(fav_color)  # Given as string
    col_1 = [element * 255 for element in col_1]
    col_2 = animal(animal_ani)
    vector = col_1 + col_2
    vec_as_str = ""
    for i in vector:
        addition = str(int(i)) + " "
        vec_as_str += addition
    vector = vec_as_str[:-1]  # remove last " "
    print("user vector", vector)
    return vector # list
    
    
def send_to_queue2(vector, genre, username, user_email):
    mbody = "Client recommendation request" + str(random.random())
    attr = {
        'vector': {
            'DataType': 'String',
            'StringValue': str(vector)
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
    print("SENT to queue:", response.get('MessageId'))
    return response


def test():
    vector = "101"
    genre = "hiphop"
    username = "test"
    user_email = "hey@gmail.com"
    ret = send_to_queue2(vector, genre, username, user_email)
    print("sending to queue response:", ret)
    return ret


def lambda_handler(event, context):
    # Get user_vector from event
    # Read rec and genre from queue
    messagebody = 'no message'
    for message in event['Records']:
        stuff = ''
        print(message)
        if len(message)>0: #is not None:
            # Get vector and genre from message
            animal = message['messageAttributes']['animal']['stringValue']
            fav_color = message['messageAttributes']['fav_color']['stringValue']
            genre = message['messageAttributes']['genre']['stringValue']
            username = message['messageAttributes']['username']['stringValue']
            user_email = message['messageAttributes']['user_email']['stringValue']
            vector = create_vector(animal, fav_color)
            # send to queue2
            ret = send_to_queue2(vector, genre, username, user_email)
            print("sending to queue response:", ret)
            return ret
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
