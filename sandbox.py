import falcon
import json
import pymongo
from bson import ObjectId


class Resource(object):
    def __init__(self):
        self.mdb = pymongo.MongoClient("mongodb://localhost:27017/gitsandbox")
        self.db = self.mdb.gitsandbox



    def on_post(self, req, resp):
        if req.content_length:
            doc = json.load(req.stream)
        if 'push' not in doc or 'actor' not in doc or 'repository' not in doc :
            raise falcon.HTTPBadRequest("Invalid payload received: %s" % doc)
    
        actor = doc['actor']
        repository = doc['repository']
        changes = doc['push']['changes']

        commits = doc['push']['changes'][0]['commits'][0]

        original_id = ObjectId()

        if not self.db.repository.find_one({'key': repository['full_name']}):
            self.db.repository.insert_one({
                '_id': original_id,
                'provider': 'bitbucket',
                'key': repository['full_name'],
                'url': repository['links']['self']['href'],
                'private': repository['is_private'],
            })

            #print('[%s]' % ', '.join(map(str, repository)))

            self.db.commits.insert({
                'repository_id': original_id,
                'hash': commits['hash'],
                'date': commits['date'],
                'message': commits['message'],
                'author': commits['author']['raw'],

            })
            #print('[%s]' % ', '.join(map(str, commits)))

            self.db.commits.aggregate([
                {
                    "$lookup":
                        {
                            "from": "repository",
                            "localField": "repository_id",
                            "foreignField": "_id",
                            "as": "test"
                        }
                }
            ])


        resp.status = falcon.HTTP_200  # This is the default status
        resp.body = ('Okey')


app = falcon.API()

# things will handle all requests to the '/things' URL path
app.add_route('/webhook', Resource())
