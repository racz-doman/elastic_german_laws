try:
    import os
    import sys
    import elasticsearch
    from elasticsearch import Elasticsearch

    print("All Modules Loaded!\n")
except Exception as e:
    print("Some Modules are missing {}\n".format(e))

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

if es.ping():
    print("Elasticsearch is working properly.\n")
else:
    print("There is a problem with Elasticsearch.\n")

es.indices.create(index='console_law', body={
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0
  }
})

print("Index created successfully.\n")
print("All the indices:\n")
res = es.indices.get_alias("*")
for Name in res:
    print(Name)

