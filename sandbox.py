import argparse
import json
import subprocess
from sqlite3.dbapi2 import Date

import falcon
import pymongo
import requests
from bson import ObjectId
from pymongo import MongoClient
import urllib.request
from unidiff import PatchSet

class Resource(object):

    def __init__(self):

        #self.mdb = pymongo.MongoClient("mongodb://git_skander:git_skander311@192.168.17.128/gitsandbox")
        self.mdb = pymongo.MongoClient("mongodb://192.168.17.128:27017/gitsandbox")
        #self.mdb = pymongo.MongoClient("mongodb+srv://skander:Skander311@cluster0.f5hb3.mongodb.net/<dbname>?retryWrites=true&w=majority")
        self.db = self.mdb.gitsandbox

    def on_post(self, req, resp):
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

        if not self.db.commits.find_one({'hash': commits['hash']}):
            self.db.commits.insert({
                '_id': orginal_id_commit,
                'repository_id': original_id_repo,
                'hash': commits['hash'],
                'date': commits['date'],
                'message': commits['message'],
                'href': commits['links']['self']['href'],
                'type': commits['type'],
            })
            print(commits['date'])
            self.db.users.insert({
                '_id': orginal_id_user,
                'commit_id': orginal_id_commit,
                'name': users['display_name'],
                'type': users['type'],
            })

            diff = commits['links']['diff']['href']
            diff_stat = (diff.replace('diff', 'diffstat'))
            r = requests.get(diff_stat)
            doc = r.json()
            files = doc['values'][0]
            type_file = files['status']

            if type_file == "modified":
                self.db.files.insert({
                    'commit_id': orginal_id_commit,
                    'status': files['status'],
                    'type_commit': files['type'],
                    'old_name': files['old']['path'],
                    'new_name': files['new']['path'],
                    'linesremoved': files['lines_removed'],
                    'linesadded': files['lines_added'],
                    'lines ': files['lines_added'] - files['lines_removed'],
                })
            elif type_file == "added":
                self.db.files.insert({
                    'commit_id': orginal_id_commit,
                    'status': files['status'],
                    'type_commit': files['new']['type'],
                    'new_name': files['new']['path'],
                    'linesremoved': files['lines_removed'],
                    'linesadded': files['lines_added'],
                    'lines ': files['lines_added'],
                })
            else:
                self.db.files.insert({
                    'commit_id': orginal_id_commit,
                    'status': files['status'],
                    'type_commit': files['old']['type'],
                    'old_name': files['old']['path'],
                    'linesremoved': files['lines_removed'],
                    'linesadded': files['lines_added'],
                    'lines ': files['lines_added'] + files['lines_removed'],
                })
        patch = commits['links']['patch']['href']
        page = urllib.request.urlopen(patch)
        patch_f = PatchSet(page, encoding='utf-8')

        print(patch_f[0])
        print(patch_f[0].added)
        print(patch_f[0].removed)
        print(patch_f[0].is_added_file)
        print(patch_f[0].is_removed_file)

        client = MongoClient(
            'mongodb://localhost:27017/?readPreference=primary&appname=MongoDB%20Compass&ssl=false')

        result_1 = client['gitsandbox']['commits'].aggregate([
            {
                '$lookup': {
                    'from': 'repository',
                    'localField': 'repository_id',
                    'foreignField': '_id',
                    'as': 'agg_repo_commits'
                }
            }
        ])
        result_2 = client['gitsandbox']['files'].aggregate([
            {
                '$lookup': {
                    'from': 'commits',
                    'localField': 'commit_id',
                    'foreignField': '_id',
                    'as': 'agg_files_commits'
                }
            }
        ])
        result_3= client['gitsandbox']['users'].aggregate([
            {
                '$lookup': {
                    'from': 'commits',
                    'localField': 'commit_id',
                    'foreignField': '_id',
                    'as': 'agg_users_commits'
                }
            }
        ])
        print(result_1)
        print(result_2)
        print(result_3)


        '''
                path = '/home/skander/workspace/git-sandbox'
                my_repo = git.Repo(path)
                commits_list = list(my_repo.iter_commits())
                for i in commits_list:
                    print(i)

                changed_files = []
                length = len(commits_list)
                for j in range(length):
                    for x in commits_list[j].diff(commits_list[j-1]):
                        if x.a_blob.path not in changed_files:
                            changed_files.append(x.a_blob.path)
                        if x.b_blob is not None and x.b_blob.path not in changed_files:
                            changed_files.append(x.b_blob.path)
                    print(changed_files)

                cursor = self.db.commits
                hash_list = []
                for doc in cursor.find():
                    hash_list += [doc["hash"]]
                    print("hash_list:", hash_list)
                '''

        '''
                empty_tree = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

                path = '/home/skander/workspace/git-sandbox'
                repo = git.Repo(path)

                for commit in repo.iter_commits('master'):
                    parent = commit.parents[0] if commit.parents else empty_tree
                    diffs = {
                        diff.a_path: diff for diff in commit.diff(parent)
                    }
                    for objpath, stats in commit.stats.files.items():
                        diff = diffs.get(objpath)

                        if not diff:
                            for diff in diffs.values():
                                if diff.b_path == path and diff.renamed:
                                    break

                        stats.update({
                            'object': os.path.join(path, objpath),
                            'commit': commit.hexsha,
                            'summary': commit.summary,
                            'author': commit.author.name,
                            'author-email': commit.author.email,
                            'timestamp': commit.authored_datetime,
                            'type': diff.change_type,
                            'size': commit.size,
                        })

                        print('#####')
                        print(stats)
                        print('#####')

                    # if not self.db.commits.find_one({stats['commit']: commits['hash']}):
                    self.db.files.insert({
                        'file name': stats['object'],
                        'hash': stats['commit'],
                        'commit message': stats['summary'],
                        'author': stats['author'],
                        'author email': stats['author-email'],
                        'date': stats['timestamp'],
                        'insertions': stats['insertions'],
                        'deletions': stats['deletions'],
                        'lines': stats['lines'],
                        'type': stats['type'],
                        'size': stats['size'],

                    })

        '''

        resp.status = falcon.HTTP_200  # This is the default status
        resp.body = ('Okey')


app = falcon.API()

app.add_route('/webhook', Resource())
