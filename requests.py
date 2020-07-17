import http.client

conn = http.client.HTTPSConnection('api.pipedream.com')
conn.request("GET", '/v1/sources/dc_ZduR6y/event_summaries?expand=event', '', {
  'Authorization': 'Bearer 43c6ae0fad3a3e1afcb3e501e2a8586e',
})

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))
