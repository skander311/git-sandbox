import argparse
import json
import subprocess
import falcon
import pymongo
import requests
from bson import ObjectId
from pymongo import MongoClient
import urllib.request
from unidiff import PatchSet

class Resource(object):

    def __init__(self):

         self.mdb = pymongo.MongoClient("mongodb://skander:123456o@127.0.0.1:27017/gitsandbox?authSource=admin")
         self.db = self.mdb.gitsandbox

    def on_post(self, req, resp):
        print("am here !")
        global commit, stats, s
        if req.content_length:
            doc = json.load(req.stream)
        if 'push' not in doc or 'actor' not in doc or 'repository' not in doc:
            raise falcon.HTTPBadRequest("Invalid payload received: %s" % doc)

        actor = doc['actor']
        repository = doc['repository']
        changes = doc['push']['changes']
        commits = doc['push']['changes'][0]['commits'][0]
        users = doc['actor']

        original_id_repo = ObjectId()
        orginal_id_commit = ObjectId()
        orginal_id_user = ObjectId()

        repo_git = self.db.repository.find_one({'key': repository['full_name']})

        if not repo_git:
            self.db.repository.insert_one({
                '_id': original_id_repo,
                'provider': 'bitbucket',
                'key': repository['full_name'],
                'url': repository['links']['self']['href'],
                'private': repository['is_private'],
            })
        else:
            original_id_repo = repo_git['_id']

        patch = commits['links']['patch']['href']
        page = urllib.request.urlopen(patch, auth('skander.hmad@esprit.tn', 'Skander311'))
        patch_f = PatchSet(page, encoding='utf-8')

        if not self.db.commits.find_one({'hash': commits['hash']}):
            self.db.commits.insert({
                '_id': orginal_id_commit,
                'repository_id': original_id_repo,
                'hash': commits['hash'],
                'date': commits['date'],
                'message': commits['message'],
                'href': commits['links']['self']['href'],
                'type': commits['type'],
                'filesadded' : len(patch_f.added_files),
                'filesremoved' : len(patch_f.removed_files),
                'filesmodified' : len(patch_f.modified_files),

            })
            self.db.users.insert({
                '_id': orginal_id_user,
                'commit_id': orginal_id_commit,
                'name': users['display_name'],
                'type': users['type'],
            })

            diff = commits['links']['diff']['href']
            diff_stat = (diff.replace('diff', 'diffstat'))
            r = requests.get(diff_stat, auth('skander.hmad@esprit.tn', 'Skander311'))
            doc = r.json()
            i = 0
            while i < len(doc['values']):
                files = doc['values'][i]
                if doc['values'][i]['status'] == "modified":
                    self.db.files.insert({
                        'commit_id': orginal_id_commit,
                        'status': files['status'],
                        'type_commit': files['type'],
                        'old_name': files['old']['path'],
                        'new_name': files['new']['path'],
                        'linesremoved': files['lines_removed'],
                        'linesadded': files['lines_added'],
                        'lines': files['lines_added'] - files['lines_removed'],
                    })
                elif doc['values'][i]['status'] == "added":
                    self.db.files.insert({
                        'commit_id': orginal_id_commit,
                        'status': files['status'],
                        'type_commit': files['new']['type'],
                        'new_name': files['new']['path'],
                        'lines removed': files['lines_removed'],
                        'linesadded': files['lines_added'],
                        'lines': files['lines_added'],
                    })
                else:
                    self.db.files.insert({
                        'commit_id': orginal_id_commit,
                        'status': files['status'],
                        'type_commit': files['old']['type'],
                        'old_name': files['old']['path'],
                        'linesremoved': files['lines_removed'],
                        'linesadded': files['lines_added'],
                        'lines': files['lines_added'],
                    })
                i += 1
        

        resp.status = falcon.HTTP_200  # This is the default status
        resp.body = ('Okey')


app = falcon.API()

app.add_route('/webhook', Resource())
