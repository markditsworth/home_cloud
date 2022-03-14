import requests
import re

regex = "(?P<key>[^:]+): (?P<value>[^,]+),? ?"
pattern = re.compile(regex)

def searchEs(from="now-1d",to="now",es_address="http://monitor.lan:9200", index="filebeat-8.0.0-rc2"):
    url = f"{es_address}/{index}/_search"
    query = {
        "query":{
            "bool":{
                "must":[
                    {
                        "range":{
                            "@timestamp":{
                                "gte":from,
                                "lt":to
                            }
                        }
                    },
                    {
                        "query_string":{
                            "query":"message:Jellyfin.Api.Helpers.MediaInfoHelper AND message:Path"
                        }
                    }
                ]
            }
        }
    }
    r = requests.post(url, json=query)
    assert r.status_code < 300
    return r.json()

def parseLog(log):
    split_log = log.split("Jellyfin.Api.Helpers.MediaInfoHelper: ")[1]
    matches = pattern.findall(split_log)
    assert len(matches) > 0
    parsed_result = dict(matches)
    return parsed_result["Path"].strip('"').strip("'")

def extractMedia(path):
    split_path = path.split("/")
    if split_path[3] == "TV":
        # tv
        series_name = split_path[4]
        seasson_number = split_path[5]
    elif split_path[3] == "Movies":
        # movies
        movie_name = split_path[4]