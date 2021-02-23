try:
    import os
    import sys
    import elasticsearch
    from elasticsearch import Elasticsearch, helpers

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
res = es.indices.get_alias()
for Name in res:
    print(Name)

with open("laws.txt", encoding='utf-8') as f:
    all_laws = f.readlines()
all_laws = [x.strip() for x in all_laws]


def generator(data):
    for law in data:
        yield {
            "_index": "console_law",
            "law": law,
        }


try:
    result = helpers.bulk(es, generator(all_laws))
    print("Data successfully uploaded.")
except Exception as e:
    print("Something went wrong during upload {}".format(e))

