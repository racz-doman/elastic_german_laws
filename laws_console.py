try:
    from elasticsearch import Elasticsearch
except Exception as e:
    print("Importing failed {}".format(e))

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

if es.ping():
    print("Elasticsearch is working properly.\n")
else:
    print("There is a problem with Elasticsearch.\n")

print("What do you want to search for? (E.g. N4192513665P)")
question = input()

body = {
    "_source": "law",
    "size": 3,
    "query": {
        "match_phrase": {
            "law": '"' + question + '"'
        }
    }
}

result = es.search(index='console_law', body=body)
print("The result:\n")
print(result)
print("The law:\n")
print(result['hits']['hits'][0]['_source']['law'])
