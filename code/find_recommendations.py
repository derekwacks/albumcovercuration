import json
from sklearn.neighbors import NearestNeighbors
import numpy as np
import boto3


access_key_id = os.environ['access_key_id']
secret_access_key = os.environ['secret_access_key']

s3 = boto3.client('s3', aws_access_key_id=access_key_id,
                  aws_secret_access_key=secret_access_key,
                  region_name="us-west-2")
                  

lambda_client = boto3.client('lambda', aws_access_key_id=access_key_id,
                  aws_secret_access_key=secret_access_key,
                  region_name="us-west-2")
                  



def load_txt(genre, testing_bool):
    """
    Loads vectors from a text file.
    :param testing_bool: if True, loads local .txt testing file
                         else, loads from S3 bucket
    :return:
    """
    vec_bucket_name = "cover-art-vectors"
    vectors = {}
    keyids = []
    vector_array = []
    if testing_bool == True:
        filename = str(genre) + 'albums.txt'
        for line in open(filename, 'r').readlines():
            splits = line.strip().split()
            key = str(splits[0].decode("utf-8"))
            vectors[key] = np.array([float(x) for x in splits[1:]])
            vector_array.append(np.array([float(x) for x in splits[1:]]))
    else:
        # Specify the file filled with albums of that genre
        TOT_album_vector_file = genre + '_albums.txt'
        # Load from S3
        print("getting from", TOT_album_vector_file)
        album_file = s3.get_object(Key=TOT_album_vector_file, Bucket=vec_bucket_name)
        album_file_r = album_file['Body'].iter_lines()
        print(album_file_r)
        for line in album_file_r:
            splits = line.strip().split()
            arr = np.array([int(x) for x in splits[1:]])
            key = str(splits[0].decode("utf-8"))
            vectors[key] = arr
            vector_array.append(arr)
            keyids.append(key) # array of id's
            print("line", key, arr)
            
    vector_array = np.array(vector_array)
    return vectors, vector_array, keyids

   
# SWITCHOVER  
def get_recs(user_vector, genre, username, email):    
    testing_bool = False
    vectors, vector_array, keyids = load_txt(genre, testing_bool)
    recs = []
    user_answers = user_vector
    N_KNN = 11
    knn = NearestNeighbors(n_neighbors=N_KNN)
    knn.fit(vector_array)  # instead of z
    print("vector_array", vector_array)  # 2d np array
    print("user_answers", user_answers)
    neighbor_radii, neighbors = knn.kneighbors([user_answers], N_KNN,
                                               return_distance=True)  # get nearest neighbors to point
    neighbors = neighbors[0] #[1:]  # get inner list of neighbors without counting node itself as its own neighbor
    print("neighbors:", neighbors)
    for index in neighbors:
        recs.append(keyids[index])
    
    # SWITCHOVER
    # PREPEND username and email
    recs.insert(0, email)
    recs.insert(0, username)

    # send as string instead of list
    str1 = " " 
    recs = (str1.join(recs))
    
    return recs

def testing():
    vector_str = "221 199 105  36  42  40"
    genre = "hiphop"
    vector = [int(i) for i in vector_str.split()]
    vector = np.array(vector)
    print(vector_str, "->", vector)
    recs = get_recs(vector, genre)
    print(recs)
    
    
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
        FunctionName='playlist_curator_from_queue',
        InvocationType='RequestResponse',
        Payload=js #data, #b'bytes'|file,
        #Qualifier='string'
    )
    resp = json.loads(json.dumps(resp, default=str))
    return resp


def lambda_handler(event, context):
    

    # Get user_vector from event
    # READ rec and genre FROM queue!
    messagebody = 'no message'
    for message in event['Records']:
        stuff = ''
        print(message)
        print(message)
        if len(message)>0: #is not None:

            # Get vector and genre from message
            vector_str = message['messageAttributes']['vector']['stringValue']
            genre = message['messageAttributes']['genre']['stringValue']
            username = message['messageAttributes']['username']['stringValue']
            user_email = message['messageAttributes']['user_email']['stringValue']
            print("User Info:", username, user_email)
            
           # "0 10 11 12" -> [0, 10, 11, 12] str to list of ints
            vector = [int(i) for i in vector_str.split()]    
        
            print(vector_str, "->", vector)
            print("AT END ", vector, genre)
            
            recs = get_recs(vector, genre, username, user_email)
            print(type(recs), type(recs[0]))
            print("RECS", recs) # list of lists (each sublist is a vec)
            print("len", len(recs))
            
            ### pass album id's from recommendation to playlist maker lambda
            ### "playlist_curator_from_queues"
            resp = send_to_next_lambda(recs)
            print("From lambda:", resp)
            #return recs, username, user_email  # list of entry id's
            return resp 