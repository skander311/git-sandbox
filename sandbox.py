import falcon
import json
import pymongo

class Resource(object):
    def __init__(self):
        self.mdb = pymongo.MongoClient("mongodb://localhost:27017/gitsandbox")
        self.db = self.mdb.gitsandbox

    def on_post(self, req, resp):
        if req.content_length:
            doc = json.load(req.stream)
        if 'push' not in doc or 'actor' not in doc or 'repository' not in doc:
            raise falcon.HTTPBadRequest("INvalid payload received: %s" % doc)
    
        actor = doc['actor']
        repository = doc['repository']
        changes = doc['push']['changes']

        if not self.db.repository.find_one({'full_name': repository['full_name']}):
            self.db.repository.insert_one({
                'provider': 'bitbucket',
                'key': repository['full_name'],
                'url': repository['links']['self']['href'],
                'private': repository['is_private'],
            })

        resp.status = falcon.HTTP_200  # This is the default status
        resp.body = ('Okey')


app = falcon.API()

# things will handle all requests to the '/things' URL path
app.add_route('/webhook', Resource())
