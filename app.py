import redis
from pymongo import MongoClient
from flask import Flask, jsonify, request
import pickle
import numpy as np
from scipy import spatial
from functions import get_sim, add_user
import os

app = Flask(__name__)
cluster = MongoClient(os.getenv('MONGO_URL'))
redisClient = redis.from_url(url=os.getenv('REDIS_URL'),charset='utf-8',decode_responses=True)

col = cluster.Users.User_Embeddings
folCollection = cluster.Users.Follows


@app.route('/')
def home():
    return "User Recommendation API"

@app.route('/recommend',methods=['GET'])
def recommend():        
    data = request.get_json()
    if redisClient.exists(data['user_id']) == False:
        add_user(data['user_id'],col,redisClient)
    recommended_users = list(redisClient.zrange(data['user_id'],0,99))    
    return jsonify({"users":recommended_users})

@app.route('/newuser',methods=['GET'])
def newuser():        
    data = request.get_json()
    user_id = data['user_id']
    vector = np.zeros((517))
    categories = pickle.load(open('./categories.pkl','rb'))
    user_embed = pickle.load(open('./user_embed.pkl','rb'))

    for category in data['categories']:
        if categories.get(category,-1) != -1:
            vector[categories[category]] += 2        

    
    embed = np.matmul(vector,user_embed)
    del user_embed
    del categories
    col.insert_one({'user_id':user_id,'user_embed':list(embed)})
    
    return "Added user"

@app.route('/follows',methods=['POST'])
def follows():
    data = request.get_json()
    user_id = data['user_id']
    followees = data['followees_id']
    redisClient.zrem(user_id,*followees)
    foldict = [{'user_id':x,'follower_id':user_id} for x in followees]
    folCollection.insert_many(foldict)

if __name__ == "__main__":
    app.run(debug=True)

