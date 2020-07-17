import falcon
from json import dumps

class VerifierResource():
    def on_post(self, req, resp):
        def on_post(self, req, resp):
	posted_data = json.loads(req.stream.read())
	print(str(type(posted_data)))
	print(posted_data)

api = falcon.API()
api.add_route('/verify', VerifierResource())
