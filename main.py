from dotenv import load_dotenv
import os
import base64
from requests import post, get
import json
import networkx as nx
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

# Function to get tokens
def get_token():
    auth_string = f"{client_id}:{client_secret}"
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
    query = f"?q={artist_name}&type=artist&limit=1"

    query_url = url + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)["artists"]["items"]

    if len(json_result) == 0:
        print(f"No artist found with the name: {artist_name}")
        return None
    
    return json_result[0]

# function to get related artists
def get_related_artists(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/related-artists"
    headers = get_auth_header(token)
    result = get(url, headers=headers)

    if result.status_code == 200:
        json_result = json.loads(result.content)["artists"]
        return json_result
    else:
        print(f"Error in get_related_artists request for artist_id {artist_id}. Status code: {result.status_code}")
        print(result.text)
        return None

# Read artist names from a file
with open("artist_names.txt", "r", encoding="utf-8") as file:
    artist_names = file.read().splitlines()

# Create a directed graph using networkx
graph = nx.DiGraph()

# Call the functions for each artist and add edges to the graph
token = get_token()

for source_artist_name in artist_names:
    print(f"Processing artist: {source_artist_name}")
    source_result = search_for_artist(token, source_artist_name)

    if source_result:
        source_artist_id = source_result["id"]
        related_artists = get_related_artists(token, source_artist_id)

        for related_artist in related_artists:
            target_artist_name = related_artist["name"]
            graph.add_edge(source_artist_name, target_artist_name)

# Save the graph to a GraphML file
nx.write_graphml(graph, "spotify_network.graphml")
print(f"Number of nodes: {graph.number_of_nodes()}")
print(f"Number of edges: {graph.number_of_edges()}")
