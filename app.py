import redis
from pymongo import MongoClient
from flask import Flask, jsonify, request, send_from_directory, url_for
import pickle
import numpy as np
from scipy import spatial
from functions import get_sim, add_user
import os

app = Flask(__name__)

''' Recommendation MongoDB URI '''
cluster = MongoClient('mongodb+srv://nirmal:2000@cluster0-2aasp.mongodb.net/<dbname>?retryWrites=true&w=majority')

redisClient = redis.Redis(charset='utf-8',decode_responses=True)

''' Collection cursors from recommendation database '''
col = cluster.Users.User_Embeddings
folCollection = cluster.Users.Follows
posted = cluster.Users.Posted


@app.route('/')
def home():
    return '''<html><title>User Recommendation</title>
              <body><h3>User Recommendation API </h3></body></html>'''

@app.route('/recommend',methods=['GET'])
def recommend():
    data = request.get_json()
    if redisClient.exists(data['user_id']) == False:
        add_user(data['user_id'],col,redisClient,posted)
    recommended_users = list(redisClient.zrange(data['user_id'],0,99))
    return jsonify({"users":recommended_users})

@app.route('/newpost',methods=['POST'])
def newpost():
    data = request.get_json()
    user_id = data['user_id']
    posted.insert_one({'user_id':user_id})
    redisClient.mset({user_id+'_post':'1'})
    return "Updated"

@app.route('/newuser',methods=['GET'])
def newuser():
    data = request.get_json()
    user_id = data['user_id']
    
    ''' Loading categories dictionary from hard disk '''
    categories = pickle.load(open('categories.pkl','rb'))
    vector = np.zeros((len(categories)))

    ''' Loading Embedding Matrix from hard disk '''
    user_embed = pickle.load(open('user_embeddings.pkl','rb'))

    for category in data['categories']:
        if categories.get(category,-1) != -1:
            vector[categories[category]] +=2

    embed = np.matmul(vector,user_embed)
    del user_embed
    del categories

    ''' Inserting new user's embedding to User_Embeddings '''
    col.insert_one({'user_id':user_id,'user_embed':list(embed)})

    return "Added user"

@app.route('/follows',methods=['POST'])
def follows():
    data = request.get_json()
    user_id = data['user_id']
    followees = data['followees_id']
    redisClient.zrem(user_id,*followees)
    foldict = [{'user_id':x,'follower_id':user_id} for x in followees]

    ''' Adding follower-followee pair to Follows collection '''
    folCollection.insert_many(foldict)
    return "Updated"

@app.route('/train',methods=['GET','POST'])
def train():
    redisClient.flushdb()
    return "Cache flushed"

if __name__ == "__main__":
    app.run(debug=True)

