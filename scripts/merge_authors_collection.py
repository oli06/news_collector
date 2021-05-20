#update script to extract authors from article collection and insert (and reference) in to new collection
from pymongo import MongoClient
import pandas as pd
import itertools
import numpy as np

def _connect_mongo(host, port, username, password, db):
    if username and password:
        mongo_uri = 'mongodb://%s:%s@%s:%s/%s' % (username, password, host, port, db)
        conn = MongoClient(mongo_uri)
    else:
        conn = MongoClient(host, port)

    return conn[db]

def match_index(row):
    out = []
    for aref in row['authors']:
        id_match = db[new_authors_collection_name].find_one({'author': aref})
        out.append(id_match['_id'])
    return out

db_name = 'news'
article_collection_name = 'articles'
new_authors_collection_name = 'authors'
db = _connect_mongo(host='localhost', port=27017, username=None, password=None, db=db_name)

cursor = db[article_collection_name].find({})

df =  pd.DataFrame(list(cursor))

#df.authors contains nan values (no one knows why......)
#since it is type object/list, we can not simply use replace(np.nan, [])
#therefore we must check the type for every row
df['authors'] = df['authors'].apply(lambda d: d if isinstance(d, list) else [])

#making df.authors to values of type list, we can iterate over all lists in df.authors and create a unique collection 
names, counts = np.unique([*itertools.chain.from_iterable(df.authors)], return_counts=True)

#insert author, agency correlation into new collection
for n in names:
    d = db[article_collection_name].find({'authors': n}, {"agency": 1}, limit=1)
    db[new_authors_collection_name].insert_one({'author': n, 'agency': d[0]['agency']})

df['authors'] = df.apply(match_index, axis=1)

#add new field
db[article_collection_name].update_many({}, {"$set": {"author_refs": 1}})

#insert objectIds 
for index, row in df.iterrows():
    db[article_collection_name].update_one({'_id': row['_id']}, {"$set": {"author_refs": row['authors']}})

print("done")