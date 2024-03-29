from dotenv import load_dotenv
import os
import base64
from requests import post, get
import json
import networkx as nx
import time

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

# Function to search for artist and get artist details
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
    
    artist_details = json_result[0]
    followers = artist_details.get("followers", {}).get("total", 0)
    genres = artist_details.get("genres", [])

    return {"id": artist_details["id"], "followers": followers, "genres": genres}

# Function to get all albums of an artist
def get_all_albums(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
    headers = get_auth_header(token)
    params = {"limit": 5}  # You can adjust the limit parameter based on your needs
    result = get(url, headers=headers, params=params)

    if result.status_code == 200:
        json_result = json.loads(result.content)["items"]
        return json_result
    elif result.status_code == 429:
        # Retry after the specified duration
        retry_after = int(result.headers.get('Retry-After', 1))
        print(f"Rate limit exceeded. Retrying after {retry_after} seconds.")
        time.sleep(retry_after)
        return get_all_albums(token, artist_id)
    else:
        print(f"Error in get_all_albums request for artist_id {artist_id}. Status code: {result.status_code}")
        return None

# Function to process an album and get collaborators
def process_album(token, album, artist_name, graph):

    artist_details = search_for_artist(token, artist_name)
    if not artist_details:
        return

    # Convert genres to a string
    genres_str = ", ".join(artist_details["genres"])

    # Add nodes for the artist with followers and genres attributes
    graph.add_node(artist_name, followers=str(artist_details["followers"]), genres=genres_str)

    album_id = album["id"]
    url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
    headers = get_auth_header(token)
    result = get(url, headers=headers)

    if result.status_code == 200:
        tracks = json.loads(result.content)["items"]

        # Iterate through each track and get collaborators
        for track in tracks:
            track_id = track["id"]
            url = f"https://api.spotify.com/v1/tracks/{track_id}"
            result = get(url, headers=headers)

            if result.status_code == 200:
                json_result = json.loads(result.content)
                artists = json_result.get('artists', [])
                collaborators = [artist['name'] for artist in artists if artist['name'] != artist_name and artist['name'] in artist_names_set]

                # Add nodes for collaborators to the graph
                for collaborator in collaborators:
                        graph.add_node(collaborator)
                        # Increment the weight of the edge or create a new one
                        if graph.has_edge(artist_name, collaborator):
                            graph[artist_name][collaborator]['weight'] += 1
                        else:
                            graph.add_edge(artist_name, collaborator, weight=1)



# Read artist names from a file and convert to a list and a set
with open("artist_names.txt", "r", encoding="utf-8") as file:
    artist_names_list = file.read().splitlines()

# Create a set for efficient membership check
artist_names_set = set(artist_names_list)

# Load existing graph from GraphML file
graph_file = "spotify_network.graphml"
if os.path.exists(graph_file):
    graph = nx.read_graphml(graph_file)
else:
    graph = nx.DiGraph()

# Call the functions for each artist
token = get_token()

# Main Execution
try:
    for artist_name in artist_names_list:
        print(f"\nSearching for artist: {artist_name}")
        result = search_for_artist(token, artist_name)

        if result:
            artist_id = result["id"]

            # Get all albums of the artist
            albums = get_all_albums(token, artist_id)

            if albums:
                # Iterate through each album and get collaborators
                for album in albums:
                    process_album(token, album, artist_name, graph)

except KeyboardInterrupt:
    # Export the graph to GraphML format 
    nx.write_graphml(graph, graph_file)
    print(f"\nGraph exported to {graph_file}")
    print("Script interrupted. Exiting...")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Export the graph to GraphML format
    nx.write_graphml(graph, graph_file)
    print(f"\nGraph exported to {graph_file}")
