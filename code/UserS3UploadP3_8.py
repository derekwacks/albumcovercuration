import colorthief
#import colorthief.ColorThief
from colorthief import ColorThief
from PIL import Image
from urllib.request import urlopen
import io
import ssl

import boto3
from decimal import Decimal
import os
import json
import urllib
import urllib.parse
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

access_key_id = os.environ['access_key_id']
secretkey = os.environ['secretkey']
region = "us-west-2"
img_bucket_name = "albumprojectup195958-dev"
s3 = boto3.client('s3', aws_access_key_id=access_key_id, aws_secret_access_key = secretkey, region_name = region )


#Setting up SQS

queue_name = "music_rec_queue2"

sqs = boto3.resource('sqs', aws_access_key_id = access_key_id,
    aws_secret_access_key = secretkey)
    
# Get the queue. This returns an SQS.Queue instance
queue = sqs.get_queue_by_name(QueueName=queue_name)
print(queue.url)
print(queue.attributes.get('DelaySeconds'))


print('Loading function')



def create_vector(palette_vec):
    # palette_vec is a list of two tuples [(255, 255, 255), (255, 255, 255)]
    col_1 = palette_vec[0]
    col_2 = palette_vec[1]
    vector = list(col_1) + list(col_2)
    vec_as_str = ""
    # items in vector are floats 
    for i in vector:
        addition = str(int(i)) + " "
        vec_as_str += addition
    vector = vec_as_str[:-1]  # remove last space " "
    print("created vector", vector)
    return vector # string 



def create_art_vector(image_key):
    """
    Given S3 key and url to photo in S3, returns vector
    :return: 1x6 color vector
    """
    print("Creating vector...")

    try:
        # Getting photo from provided url
        image_url = "https://albumprojectup195958-dev.s3-us-west-2.amazonaws.com/"+image_key
        print(image_url)
        response = s3.get_object(Bucket=img_bucket_name, Key=image_key)
        image = response['Body']
        
        ##user =  response['Metadata']['username'] ### ADDED HERE
        
        print("file read", image)
    
        # Delete image from S3 image bucket
        # put_resp = s3.put_object(ACL='public-read-write', Body=f, Bucket=img_bucket_name, Key=image_key)
        del_resp = s3.delete_object(Bucket=img_bucket_name, Key=image_key)
        print("Delete response:", del_resp)
        
        # Getting color palette 
        color_count = 5
        color_thief = ColorThief(image)
        print("color thief created")
        palette = color_thief.get_palette(color_count=color_count)
        print("palette:", palette)
        #return (palette[0:2], user)  # return top 2 colors from user's uploaded image
        return_vec = palette[0:2]
        return return_vec
    except IOError as exc:
        raise RuntimeError("Issue getting colors from image") from exc
        

def push_to_queue(vector, username, user_email):
    # Randomly select a genre here
    import random
    genres = ['hiphop', 'pop', 'alternative', 'country', 'rock']
    genre = random.choice(genres)
    
    mbody = "Client recommendation request"+str(random.random())
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
    

    response = queue.send_message(MessageBody=mbody, MessageAttributes=attr) # , MessageGroupId=groupid
    print(response.get('MessageId'))
    return response
 
 
def get_username_and_email():
    #bucket_name = "albumprojectup195958-dev"
    bucket_name = "cover-art-vectors"
    
    f_key = "user.txt"
    file = s3.get_object(Key=f_key, Bucket=bucket_name)
    file_r = file['Body'].iter_lines()
    for line in file_r: # only 1 line in file "user email@gmail.com"
        splits = line.strip().split()
        print("username", splits[0])
        print("email", splits[1])
    # Convert from bytes to string
    ret = [splits[0].decode("utf-8"), splits[1].decode("utf-8")]
    return ret


# SWITCHOUT
def parse_file_name(key):
    #Ex: public/test#test@gmail.com#djw_bird2.jpg
    key = key[7:]
    ret = key.split("#")
    username = ret[0]
    email = ret[1]
    key = ret[2]
    return username, email, key


def lambda_handler(event, context):
    print("lambda triggered!")
    # Get the object from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    
    print("Event", event)
    logger.debug("\nEvent debug "+bucket+ " "+key)
    
    try:
        # create 6d vectors from top two colors in newly uploaded user image
        # SWITCHOUT
        orig_key = key 
        username, user_email, key = parse_file_name(key)
        print("info pulled from key:", key, username, user_email)
        #ret = get_username_and_email()
        #username = ret[0]
        #user_email = ret[1]
        
        vec = create_art_vector(orig_key) #(vec, user)
        vec = create_vector(vec)
        #vec = ret[0]
        #user = ret[1]
        print("\n6d vector created: ", vec)
        # Now push vector and a random genre to the queue
        response = push_to_queue(vec, username, user_email)
        return response 
    except Exception as e:
        print(e)
        print("Error processing user uploaded image {} from bucket {}. ".format(key, bucket))
        raise e
