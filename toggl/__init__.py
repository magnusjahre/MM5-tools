import requests
import ast

def togglRequest(baseurl, params):
    r = requests.get(baseurl, params=params, auth=('223867917969fce808959853d3776185', 'api_token'))
    print r.url
    content = r.content
    content = content.replace("null", "0") #FIXME: not particularly safe, e.g. the string nullify
    data = ast.literal_eval(content)
    return data

