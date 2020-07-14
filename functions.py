
from scipy import spatial


def get_sim(i,j):
  return 1 - spatial.distance.cosine(i,j)

def add_user(key,col,redisClient,posted):
    ''' Getting all users' embeddings '''
    allCollections = list(col.find())

    ''' Getting embedding for given user_id from Collection '''
    cur_doc = list(col.find({ 'user_id' : key }))[0]

    embed = cur_doc['user_embed']

    for doc in allCollections:
        if redisClient.exists(doc['user_id']+'_post') == False:
            if posted.find({'user_id':doc['user_id']}).count()>0:
                redisClient.mset({doc['user_id']+'_post':'1'})
            else:
                redisClient.mset({doc['user_id']+'_post':'0'})

        if key != doc['user_id'] and redisClient.get(doc['user_id']+'_post') == '1':
            emb = doc['user_embed']
            sim = get_sim(embed,emb)
            if cur_doc.get('node_embed',-1)!=-1 and doc.get('node_embed',-1)!=-1:
                sim = 0.6*sim + 0.4*get_sim(cur_doc['node_embed'],doc['node_embed'])
            redisClient.zadd(key,{doc['user_id']:float(sim)})
