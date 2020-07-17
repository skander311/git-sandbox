import falcon 
from json import dumps

import http.client

conn = http.client.HTTPSConnection('api.pipedream.com')
conn.request("GET", '/v1/sources/dc_ZduR6y/event_summaries?expand=event', '', {
  'Authorization': 'Bearer 43c6ae0fad3a3e1afcb3e501e2a8586e',
})

res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))

class Resource(object):
    def on_post(self, req, resp):
      
        resp.status = falcon.HTTP_200  # This is the default status
        resp.body = ('Okey')
	

app = falcon.API()

# Resources are represented by long-lived class instances
first = Resource()

# things will handle all requests to the '/things' URL path
app.add_route('/first', first)
