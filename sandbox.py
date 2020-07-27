import json
import falcon
import pymongo
from bson import ObjectId
from pymongo import MongoClient
import git
import os

class Resource(object):
    def __init__(self):
        self.mdb = pymongo.MongoClient("mongodb://localhost:27017/gitsandbox")
        self.db = self.mdb.gitsandbox


        my_repo = git.Repo('/home/skander/workspace/git-sandbox')
        #print(my_repo)
        #diff = my_repo.git.diff(my_repo.head.commit.tree)
        commits_list = list(my_repo.iter_commits())
        print("First commit: ", commits_list[0])

        changed_files = []

        for x in commits_list[0].diff(commits_list[-1]):
            if x.a_blob.path not in changed_files:
                changed_files.append(x.a_blob.path)

            if x.b_blob is not None and x.b_blob.path not in changed_files:
                changed_files.append(x.b_blob.path)

        print(changed_files)


        #cursor = self.db.commits
        #hash_list = []
        #for doc in cursor.find():
            #hash_list += [doc["hash"]]
            #print("hash_list:", hash_list)

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


        repo_git = self.db.repository.find_one({'key': repository['full_name']})

        if not repo_git:
            self.db.repository.insert_one({
                '_id': original_id,
                'provider': 'bitbucket',
                'key': repository['full_name'],
                'url': repository['links']['self']['href'],
                'private': repository['is_private'],
            })
        else:
            original_id = repo_git['_id']

        if not self.db.commits.find_one({'hash': commits['hash']}):
            self.db.commits.insert({
                'repository_id': original_id,
                'hash': commits['hash'],
                'date': commits['date'],
                'message': commits['message'],
                'author': commits['author']['raw'],
                'href': commits['links']['self']['href'],
                'type': commits['type'],

            })



        client = MongoClient(
            'mongodb://localhost:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false')

        result = client['gitsandbox']['commits'].aggregate([
            {
                '$lookup': {
                    'from': 'repository',
                    'localField': 'repository_id',
                    'foreignField': '_id',
                    'as': 'agg'
                }
            }
        ])

        print(result)



        resp.status = falcon.HTTP_200  # This is the default status
        resp.body = ('Okey')


app = falcon.API()

# things will handle all requests to the '/things' URL path
app.add_route('/webhook', Resource())
