
import http.client
import pprint

connection = http.client.HTTPSConnection("api.pipedream.com")
connection.request("GET", "/")
response = connection.getresponse()
headers = response.getheaders()
pp = pprint.PrettyPrinter(indent=4)
pp.pprint("Headers: {}".format(headers))


