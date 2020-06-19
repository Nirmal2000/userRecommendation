
from scipy import spatial


def get_sim(i,j):  
  return 1 - spatial.distance.cosine(i,j)

def add_user(key,col,redisClient):
    allCollections = list(col.find())
    cur_doc = list(col.find({ 'user_id' : key }))[0]
    embed = cur_doc['user_embed']

    for doc in allCollections:
        if key != doc['user_id']:
            emb = doc['user_embed']
            sim = get_sim(embed,emb)
            if cur_doc.get('node_embed',-1)!=-1 and doc.get('node_embed',-1)!=-1:        
                sim = 0.6*sim + 0.4*get_sim(cur_doc['node_embed'],doc['node_embed'])
            redisClient.zadd(key,{doc['user_id']:float(sim)})