from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
@app.route("/health", methods=["GET"])
def health():
    return {"status":200}


@app.route("/count", methods=["GET"])
def count():
    try:
        # Count the number of documents in the collection
        count = db.songs.count_documents({})

        # Return the count in a JSON response
        return jsonify({"count": count, "status": 200})
    except Exception as e:
        # Handle unexpected errors and return a 500 response
        return jsonify({"error": str(e)}), 500


@app.route("/song", methods=["GET"])
def get_all_songs():
    try:
        # Fetch all songs from the collection
        songs = db.songs.find()

        # Convert the cursor to a JSON serializable list
        songs_list = json_util.dumps(songs)

        # Return the list of songs
        return jsonify({"songs": json.loads(songs_list), "status": 200})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    try:
        # Find the song by its ID
        song = db.songs.find_one({"id": id})

        if song:
            # Convert to JSON
            song_json = json_util.dumps(song)
            return jsonify({"song": json.loads(song_json), "status": 200})
        else:
            return jsonify({"message": "Song with the given ID not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/song", methods=["POST"])
def create_song():
    try:
        # Parse the request body
        song = request.get_json()

        # Check if the song already exists
        existing_song = db.songs.find_one({"id": song["id"]})
        if existing_song:
            return jsonify({"message": f"Song with id {song['id']} already exists"}), 302

        # Insert the new song into the collection
        db.songs.insert_one(song)

        return jsonify({"message": "Song created successfully", "song": song}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    try:
        # Parse the request body
        updates = request.get_json()

        # Check if the song exists
        song = db.songs.find_one({"id": id})

        if song:
            # Update the song with new data
            db.songs.update_one({"id": id}, {"$set": updates})

            # Fetch the updated song
            updated_song = db.songs.find_one({"id": id})
            updated_song_json = json_util.dumps(updated_song)
            return jsonify({"updated_song": json.loads(updated_song_json), "status": 200})
        else:
            return jsonify({"message": "Song with the given ID not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    try:
        # Attempt to delete the song by id
        delete_result = db.songs.delete_one({"id": id})

        # Check if the song was found and deleted
        if delete_result.deleted_count == 0:
            # Song not found
            return jsonify({"message": "song not found"}), 404
        else:
            # Song deleted successfully
            return "", 204  # No content response
    except Exception as e:
        # Handle unexpected errors
        return jsonify({"error": str(e)}), 500