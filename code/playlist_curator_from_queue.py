import json
import boto3
import time
from boto3.dynamodb.conditions import Key
import os
from botocore.exceptions import ClientError

TABLE_NAME = 'Curation-2asrsupzz5auhprcbtbpba72ze-dev'
access_key_id = os.environ['access_key_id']
secret_access_key = os.environ['secret_access_key']
# Derek root aws acct
DW_aws_access_key_id = os.environ['DW_aws_access_key_id']
DW_aws_secretkey = os.environ['DW_aws_secretkey']
dynamodb = boto3.client('dynamodb', aws_access_key_id=access_key_id,
                  aws_secret_access_key=secret_access_key,
                  region_name="us-west-2")
dynamodbRESOURCE = boto3.resource('dynamodb', aws_access_key_id=access_key_id,
                  aws_secret_access_key=secret_access_key,
                  region_name="us-west-2")
region = "us-west-2"
img_bucket_name = "albumprojectup195958-dev"
s3 = boto3.client('s3', aws_access_key_id=access_key_id, aws_secret_access_key = secret_access_key, region_name = region )
# Derek root aws acct
SES_sender = boto3.client('ses', aws_access_key_id=DW_aws_access_key_id,
    aws_secret_access_key = DW_aws_secretkey, region_name = "us-east-1" )
# defining vars globally
user = ""
email = ""    
      
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


def load_entries(entries):
    table = dynamodbRESOURCE.Table(TABLE_NAME)
    for entry in entries:
        print("Adding entry:", entry)
        table.put_item(Item=entry)


def get_album_data(album_id):
    table = dynamodbRESOURCE.Table("Albums_test")
    response = table.query(
        KeyConditionExpression=Key('id').eq(album_id)
    )
    print("Getting album data", album_id, response)
    response = response['Items'][0]
    print("Data:", response)
    return response


def create_entry(id, album_data): #username, artist, featured_track, top_song, genre):
    entry = {
        'id': id,
        'user': user, 
        'artist': album_data['artist'],
        'featured_track': album_data["featured_track"],
        'like': 0,
        'name': album_data['name'],
        'year': album_data['year'],
        'genre': album_data['genre']
    }
    return entry
    
    
def push_album_entries(recs_as_list, eleventh_rec):
    entries_to_push = []
    playlist_data = []
    for entry in recs_as_list:
        # Get album data from albums table
        album_data = get_album_data(entry)
        playlist_data.append(album_data)
        # Create entry for curation table
        new_entry = create_entry(entry, album_data)
        entries_to_push.append(new_entry)
    print("Pushing new entries:", entries_to_push)
    # Push album entry to curation table 
    load_entries(entries_to_push)
    print("Pushing new 11th entry:", eleventh_rec)
    eleventh_album_data = get_album_data(eleventh_rec)    
    eleventh_entry = create_entry(eleventh_rec, eleventh_album_data)
    load_entries([eleventh_entry])
    return playlist_data
    
    
def create_curation_entry(recs_as_list): #username, artist, featured_track, top_song, genre):
    id = "Cur-" + str(time.time())
    entry = {
        'id': id,
        'user': user, 
        'albumList': recs_as_list
    }
    return entry
    
    
def push_curation_entry(recs_as_list):
    # Create curation entry to push
    curation = create_curation_entry(recs_as_list)
    print("Created curation", curation)
    # need list of list because load_entires takes list of entries
    entries_to_push = [curation] 
    # Push curation entry to curation table 
    load_entries(entries_to_push)


def update_top_recs(new_top_rec):
    # Query for current rec entry 
    new_list = []
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
    if "Item" in resp.keys():
        current_top_recs = resp['Item']['albumList']
        print("Current top recs:", current_top_recs)
        if len(current_top_recs['L']) > 3:  # 4 recs at a time 
            current_top_recs = current_top_recs['L'][1:] # remove first
        else:
            current_top_recs = current_top_recs['L'] # all 1 or two 
        for item in current_top_recs:
            new_list.append(item['S'])
    new_list.append(new_top_rec)
    print("NEW top recs", new_list)
    table = dynamodbRESOURCE.Table(TABLE_NAME)
    entry = {
        'id': "Rec",
        'user': user, 
        'albumList':new_list
    }
    response = table.put_item(Item=entry)
    print("Putting new top rec:", response)
    

def create_email_html(playlist_data):
    # NOT using this version of html, using below 
    html="""
    <a href="https://www.w3schools.com/">Visit W3Schools.com!</a>
    "<html><body>Hey " + userinfo.name + ", <a href='https://s3.amazonaws.com/xxxx/xxxx.html?v=" + vKey + "'>Click here to validate this email address.</a></body></html>"
    """
    insert = ""
    for album in playlist_data:
        if album["preview_url"] != None:
            #song_link_list.append((album['name'], album['preview_url']))
            #'artist': album_data['artist'],
            #'featured_track': album_data["featured_track"]
            print("songname:", album['name'])
            print("url:", album['preview_url'])
            #https://cover-art.s3-us-west-2.amazonaws.com/00TduFxDBPEhdgEq6KLDtY.jpg
            image_url = "https://cover-art.s3-us-west-2.amazonaws.com/"+album["id"]+".jpg"
            image = "<br><img src='"+image_url+"' alt='Pic not found'>"
            new_str = image+"<br> <a href='" + album['preview_url'] + "'>" + album['featured_track'] + " by " + album['artist'] + " in " + album['name'] + "</a>"
            insert += new_str
        else:
            image_url = "https://cover-art.s3-us-west-2.amazonaws.com/"+album["id"]+".jpg"
            image = "<br><img src='"+image_url+"' alt='Pic not found'>"
            new_str = image+"<br>" + album['featured_track'] + " by " + album['artist'] + " in " + album['name'] + "</a>"
            insert += new_str        
    html = "<html><body>Hey " + user + ", here is your playlist! Note: some songs do not allow previews. <br>"+ insert +"</body></html>"
    return html
    
    
def verify_email(email):
    response = SES_sender.verify_email_identity(
        EmailAddress=email
    )
    return response
    

def send_email(email_body):
    # Verify email address identity
    AWS_REGION = "us-west-2"
    SENDER = "info@neuralgen.org"
    RECIPIENT = email
    SUBJECT = "Music Recommendation!"
    BODY_HTML = email_body 
    CHARSET = "UTF-8"
    try:
        response = SES_sender.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])
    return response


def lambda_handler(event, context):
    global user
    global email
    # Get rec as list of album id's from event
    print(event)
    recs = event['data'] # string of 11 recs separated by " "
    recs_as_list = recs.split(" ")
    print("Recs", recs_as_list)
    username = recs_as_list[0]
    email_from_list = recs_as_list[1]
    print("User info:", username, email_from_list)
    user = username
    email = email_from_list
    recs_as_list = recs_as_list[2:] # remove username and email from rec list
    new_top_rec = recs_as_list[-1] # save 11th entry 
    recs_as_list = recs_as_list[:-1] # remove 11th from main list
    playlist_data = push_album_entries(recs_as_list, new_top_rec)
    push_curation_entry(recs_as_list)
    update_top_recs(new_top_rec)
    html = create_email_html(playlist_data)
    response = send_email(html)
    print("done!")
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
