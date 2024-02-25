from dotenv import load_dotenv
import os
import base64
from requests import post, get
import json

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

# print to see if its working
# print(client_id, client_secret)

# Function to get tokens
def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

# Function to get authorization
def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

# function to search for artist and get artist id
def search_for_artist(token, artist_name):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = F"?q={artist_name}&type=artist&limit=1"

    query_url = url + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)["artists"]["items"]

    if len(json_result) == 0:
        print("No artist with this name")
        return None
    
    return json_result[0]

# function to get related artists
def get_related_artists(token, artist_id):
    url = F"https://api.spotify.com/v1/artists/{artist_id}/related-artists"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)["artists"]
    return json_result

# Call the functions
token = get_token()
result = search_for_artist(token, "Drake")
artist_id = result["id"]
related_artists = get_related_artists(token, artist_id)

# Print Statements
print ("Searched Artist:")
print(result)
print ("Related Artists:")
for idx, related_artist in enumerate(related_artists):
    print(F"{idx + 1}. {related_artist['name']}")