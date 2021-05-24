"""
rec_maker.py (for use in aws lambda cover_art_lex)
- fulfills/validates Lex
- takes user's answers to questions
- pushes user responses to queue1
"""

import boto3
import math
import dateutil.parser
import datetime
import time
import os
import logging
import random
from botocore.config import Config
import json

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
queue_name = "music_rec_queue1"
queue = sqs.get_queue_by_name(QueueName=queue_name)
print(queue.url)

# Setting up S3
s3 = boto3.client('s3', aws_access_key_id=access_key_id,
                  aws_secret_access_key=secret_access_key,
                  region_name="us-west-2")
                  

# Setting up cognito
cognito = boto3.client('cognito-idp', aws_access_key_id=access_key_id,
                     aws_secret_access_key=secret_access_key, region_name='us-west-2')
                     
                     

LEXUSERID = ""
# SWITCHOVER
username = ""
user_email = ""
    

lambda_client = boto3.client('lambda', aws_access_key_id=access_key_id,
                  aws_secret_access_key=secret_access_key,
                  region_name="us-west-2")
                  
                  
                  
def send_to_next_lambda(data):
    print("DATA", data)
    d = {
        "data" : data
    }

    js = json.dumps(d)
    print("json", js)
    
    data = bytes(js, encoding='utf-8')
    print("data sending:", data)
    
    resp = lambda_client.invoke(
        FunctionName='cover_art_lex2',
        InvocationType='Event', # async (don't wait for response)
        Payload=js #data, #b'bytes'|file,
        #Qualifier='string'
    )
    resp = json.loads(json.dumps(resp, default=str))
    return resp
    
    

def get_slots(intent_request):
    return intent_request['currentIntent']['slots']

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }

def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


""" --- Helper Functions --- """
def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')


def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }
    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def validate_rec_request(fav_color, animal, genre):

    genre_options = ["rock", "hiphop", "country", "alternative", "pop"]
    if genre is not None: 
        if genre.lower() not in genre_options:
            return build_validation_result(False, 
                                           'genre',
                                           '{} is not an option, please choose: rock, hiphop, alternative, pop, or country'.format(genre))
      
    if fav_color is not None:                                    
        try:
            col_1 = colors.to_rgb(fav_color.lower())  # Given as string
        except: # color string didn't work
            return build_validation_result(False, 
                               'color',
                               '{} is not an option, please choose a valid color'.format(fav_color))
                               
    if animal is not None: 
        # Check animal against hardcoded list
        if animal_check(animal) == False:
            return build_validation_result(False, 
                   'animal',
                   'Could not validate {}, please choose a different animal'.format(animal))
        
    return build_validation_result(True, None, None)


""" --- Functions that control the bot's behavior --- """


def animal_check(animal):
    list_of_animals = {'wallaby', 'weasel', 'crow', 'wildcat', 'alligator', 'pigeon', 'louse', 'mallard', 'ibis', 'jackal', 'monkey', 'antelope', 'mole', 'jay', 'ape', 'ram', 'crab', 'yak', 'lapwing', 'squid', 'caribou', 'goldfish', 'goat', 'clam', 'ibex', 'chicken', 'sand dollar', 'sandpiper', 'spider', 'grouse', 'peafowl', 'jellyfish', 'ant', 'turtle', 'cassowary', 'woodpecker', 'dove', 'deer', 'cockroach', 'beaver', 'albatross', 'dugong', 'dunlin', 'llama', 'meerkat', 'walrus', 'horse', 'mink', 'wasp', 'hedgehog', 'grasshopper', 'goose', 'sardine', 'chimpanzee', 'eland', 'wolf', 'fly', 'quelea', 'ferret', 'lyrebird', 'barracuda', 'cat', 'manatee', 'reindeer', 'okapi', 'panther', 'anteater', 'camel', 'swallow', 'gazelle', 'porcupine', 'crocodile', 'coyote', 'whale', 'chamois', 'elephant', 'gaur', 'hyena', 'hamster', 'moose', 'goshawk', 'shrew', 'narwhal', 'gnat', 'leopard', 'lion', 'octopus', 'dotterel', 'viper', 'bee', 'dogfish', 'quail', 'porpoise', 'hippopotamus', 'turkey', 'raven', 'badger', 'fox', 'penguin', 'worm', 'human', 'tiger', 'salamander', 'swan', 'oryx', 'kudu', 'termite', 'gull', 'gorilla', 'newt', 'seahorse', 'mandrill', 'rail', 'kouprey', 'starling', 'pony', 'locust', 'shark', 'frog', 'wren', 'alpaca', 'pheasant', 'crane', 'loris', 'tapir', 'bat', 'baboon', 'giraffe', 'mongoose', 'seal', 'kingfisher', 'finch', 'lobster', 'skunk', 'vulture', 'zebra', 'iguana', 'bird', 'cheetah', 'stingray', 'armadillo', 'heron', 'aardvark', 'tarsier', 'buffalo', 'mantis', 'elk', 'hummingbird', 'raccoon', 'opossum', 'snail', 'toad', 'partridge', 'rook', 'dinosaur', 'donkey', 'herring', 'wolverine', 'duck', 'chinchilla', 'snake', 'cattle', 'curlew', 'ostrich', 'dragonfly', 'hare', 'bison', 'magpie', 'boar', 'emu', 'goldfinch', 'otter', 'parrot', 'wombat', 'scorpion', 'dog', 'gerbil', 'cormorant', 'cod', 'cobra', 'lark', 'mosquito', 'pig', 'red panda', 'sparrow', 'dolphin', 'gnu', 'falcon', 'hornet', 'koala', 'quetzal', 'eagle', 'mouse', 'fish', 'lemur', 'rabbit', 'trout', 'kookabura', 'stinkbug', 'bear', 'mule', 'rhinoceros', 'oyster', 'owl', 'red deer', 'hawk', 'sheep', 'stork', 'echidna', 'marten', 'rat', 'capybara', 'butterfly', 'chough', 'flamingo', 'jaguar', 'woodcock', 'caterpillar', 'guanaco', 'pelican', 'squirrel', 'salmon', 'nightingale', 'kangaroo', 'eel', 'spoonbill'}
    if animal in list_of_animals:
        return True
    else:
        return False
    

def get_username_and_email():
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
    

def find_suggestion(intent_request):
    fav_color= get_slots(intent_request)["color"]
    animal= get_slots(intent_request)["animal"]
    genre= get_slots(intent_request)["genre"]
    source = intent_request['invocationSource']
    
    
    print(source)
    
    if source == 'DialogCodeHook':
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        slots = get_slots(intent_request)

        validation_result = validate_rec_request(fav_color, animal, genre)
        print("LUID", LEXUSERID, "<-")
        
        # Pos delete
        if intent_request['sessionAttributes'] is None:
            intent_request['sessionAttributes'] = {}
            intent_request['sessionAttributes']["LEXuserid"] = LEXUSERID
        

        if not validation_result['isValid']: # Validation failed
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])

        # Pass the price of the flowers back through session attributes to be used in various prompts defined
        # on the bot model.
        output_session_attributes = intent_request['sessionAttributes'] if intent_request[
                                                                               'sessionAttributes'] is not None else {}

        item_list = fav_color, animal, genre

        allIsGood = True
        for i in item_list:
            if i is None:
                allIsGood = False

        if allIsGood is True:
            output_session_attributes['Confirmed!'] = 'Request OKAY'
            output_session_attributes["LEXuserid"] = LEXUSERID

        return delegate(output_session_attributes, get_slots(intent_request))

    # Trigger lambda and pass animal, fav color, genre, LEXID to new lambda (don't wait for response) 
    # query database with LEXID
    
    ###### CALL NEXT LAMBDA HERE (comment out everything below)
    data = str(LEXUSERID)+ " " + str(animal)+ " " + str(fav_color)+ " " + str(genre)
    resp = send_to_next_lambda(data)
    ######

    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': "Your recommendation will be posted to your profile!"})



""" --- Intents --- """

def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """
    logger.debug(
        'dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    logger.debug('HERE {}'.format(intent_request['currentIntent']['name']))

    # Dispatch to your bot's intent handlers
    if intent_name == 'createCuration':
        print("In createCuration", intent_name)
        return find_suggestion(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')



def queue_test():
    # tests queue
    vector = "0 0 255 101 101 101"
    genre = "hiphop"
    username = "testUser"
    
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
        'user': {
            'DataType': 'String',
            'StringValue': str(username)
        }
    }
    response = queue.send_message(MessageBody=mbody, MessageAttributes=attr) # group id not necessary 
    print(response.get('MessageId'))
    return response



""" --- Main handler --- """
def lambda_handler(event, context):
    print("EVENT AT HANDLER:", event)
    print("CONTEXT AT HANDLER:", context)
    
    uid = event['userId']
    print("GETTING USERId:", uid)
    global LEXUSERID
    LEXUSERID = uid
    
     
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    #logger.debug('event.bot.name={}'.format(event['bot']['name']))
    #return queue_test()
    return dispatch(event)
    

