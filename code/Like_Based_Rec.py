import json
import boto3
from boto3.dynamodb.conditions import Key
import os
import random 

TABLE_NAME = 'Curation-2asrsupzz5auhprcbtbpba72ze-dev'

access_key_id = os.environ['access_key_id']
secret_access_key = os.environ['secret_access_key']
userpool_id = os.environ['userpool_id']


dynamodb = boto3.client('dynamodb', aws_access_key_id=access_key_id,
                  aws_secret_access_key=secret_access_key,
                  region_name="us-west-2")
                  
dynamodbRESOURCE = boto3.resource('dynamodb', aws_access_key_id=access_key_id,
                  aws_secret_access_key=secret_access_key,
                  region_name="us-west-2")
                  
cognito = boto3.client('cognito-idp', aws_access_key_id=access_key_id,
                  aws_secret_access_key=secret_access_key,
                  region_name="us-west-2")           
           
           
           
def get_users():
    list_of_users = []
    resp = cognito.list_users(
        UserPoolId=userpool_id,
        AttributesToGet=['email', 'sub'] 
    ) 
    for user in resp["Users"]:
        list_of_users.append(user["Username"])
    
    return list_of_users

           
            
def update_top_recs(user):
    # Query for current rec entry 
    new_list = []
    curr_rec_set = set()
    resp = dynamodb.get_item(
    TableName=TABLE_NAME,
    Key={
        'id': {
            'S': 'Rec'
        },
        'user': {
            'S': user
        }
    })
    entry_exists = False
    # Rec entry exists for this user
    if "Item" in resp.keys():
        entry_exists = True
        current_top_recs = resp['Item']['albumList']
        print("Current top recs:", current_top_recs)
        if len(current_top_recs['L']) > 3:  # 4 recs at a time 
            current_top_recs = current_top_recs['L'][1:] # remove first
        else:
            current_top_recs = current_top_recs['L'] # all 1 or two 
        for item in current_top_recs:
            new_list.append(item['S'])
            curr_rec_set.add(item['S'])
    
        
    # GET NEW REC BASED ON LIKES HERE
    new_top_rec = scan_get_rec(user)
    print(user, ":", new_top_rec)
    if new_top_rec is not None:
        # if it happens to be in curr_rec_set, we redraw
        while(new_top_rec in curr_rec_set):
            new_top_rec = scan_get_rec(user)
            

        new_list.append(new_top_rec)
    print("NEW top recs", new_list)
    
    table = dynamodbRESOURCE.Table(TABLE_NAME)
    entry = {
        'id': "Rec",
        'user': user, 
        'albumList':new_list
    }
    if len(new_list) != 0: 
        response = table.put_item(Item=entry)
        print("Putting new top rec:", response)


def get_rec(user):
    table = dynamodbRESOURCE.Table(TABLE_NAME)
    response = table.query(
        KeyConditionExpression=Key('user').eq(user) & Key('like').eq('1') # 1 should maybe be int
    )
    return response['Items']
    
    
def scan_get_rec(user):
    table = dynamodbRESOURCE.Table(TABLE_NAME)

    scan_kwargs = {
        'FilterExpression': Key('user').eq(user) & Key('like').eq(1)
        #'ProjectionExpression': "#yr, title, info.rating",
        #'ExpressionAttributeNames': {"#yr": "year"}
    }

    done = False
    start_key = None
    while not done:
        if start_key:
            scan_kwargs['ExclusiveStartKey'] = start_key
        response = table.scan(**scan_kwargs)
        start_key = response.get('LastEvaluatedKey', None)
        done = start_key is None


    # response now has a list of entries with likes
    # Get random index
    if len(response["Items"]) > 0:
        idx = random.randint(0, len(response["Items"])-1)
        selected_row = response["Items"][idx]
        artist = selected_row['artist']
        # Query Albums_test table for artist
        selection = get_new_album_entry(artist)
    else:
        selection = None
    # None or new album id
    return selection
 
    
    
def get_new_album_entry(artist):
    table = dynamodbRESOURCE.Table("Albums_test")
    scan_kwargs = {
        'FilterExpression': Key('artist').eq(artist)
    }
    done = False
    start_key = None
    while not done:
        if start_key:
            scan_kwargs['ExclusiveStartKey'] = start_key
        response = table.scan(**scan_kwargs)
        start_key = response.get('LastEvaluatedKey', None)
        done = start_key is None
    
    # Get random entry
    if len(response["Items"]) > 0:
        idx = random.randint(0, len(response["Items"])-1)
        selected_row = response["Items"][idx]
        id = selected_row['id']
        return id
    else:
        return None 


def lambda_handler(event, context):
    user_list = get_users()
    print(user_list)
    
    # For each user in the userpool, check their likes and add a rec
    for user in user_list: 
        update_top_recs(user)
        
        
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
