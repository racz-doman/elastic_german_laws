# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List
from flair.embeddings import TransformerDocumentEmbeddings
from flair.data import Sentence

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from elasticsearch import Elasticsearch, helpers
from rasa_sdk.types import DomainDict   

from rasa_sdk.events import SlotSet, FollowupAction
from rasa_sdk.forms import FormValidationAction

class ActionLawSave(Action):
    def name(self) -> Text:
        return "action_law_save"

    async def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        question = tracker.get_slot('law_keyword')
        answer = tracker.get_slot('law_answer')
        es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
        def generator(question,answere):
            yield {
                "_index": "saved_laws",
                "question": question,
                "anwsere": answere,
            }

        body_match = {
            "query": {
                "match": {
                "question": {
                        "query": question
                    }
                }
            }
        }

        result = es.search(index='saved_laws', body=body_match)

        if(result['hits']['total']['value']==0):
            try:
                helpers.bulk(es, generator(question,answer))
            except Exception as e:
                print("Something went wrong during upload {}".format(e))

        return []

class ActionLawRespond(Action):
    LAW_COUNT = 0

    def name(self) -> Text:
        return "action_law_respond"

    async def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        search_text = tracker.get_slot('law_keyword')
        search_type = tracker.get_slot('law_type')
        es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
        embedding = TransformerDocumentEmbeddings('bert-base-german-cased')

        def Convert(string):
            li = list(string.split(" "))
            return li

        def vektorositas(data):
            sentence = Sentence(Convert(data))
            embedding.embed(sentence)
            return sentence.embedding.detach().numpy()
        #"Griechenland Österreich interessieren Minimalsätze Tarif Stelle"
        veki=vektorositas(search_text)

        body_match = {
            "query": {
                "match": {
                "question": {
                        "query": search_text
                    }
                }
            }
        }
        result = es.search(index='saved_laws', body=body_match)
        lawAnswer = ""

        if(result['hits']['total']['value']!=0):
            lawAnswer= result['hits']['hits'][0]['_source']['anwsere']
            dispatcher.utter_message(lawAnswer)
        else:
            body = {
                "query": {
                    "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                            "source": "cosineSimilarity(params.query_vector, 'law_vector') + 1.0",
                            "params": {"query_vector": veki}
                        }
                    }
                }
            }
            result = es.search(index=search_type, body=body)
            lawAnswer = result['hits']['hits'][self.LAW_COUNT]['_source']['law']
            dispatcher.utter_message(lawAnswer)
            self.LAW_COUNT = self.LAW_COUNT + 1


        return [SlotSet("law_answer", lawAnswer)]

    

class ValidateLawsearchForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_lawsearch_form"

    @staticmethod
    def law_type_db() -> List[Text]:
        """Database of supported law types"""

        return ["justiz", "verfassungsgerichtshof",
                "regierungsvorlage", "gemeinderecht", "bundesnormen",
                "landesgesetzblatt", "normenliste", "begutachtungsentwürfe",
                "verwaltungsgerichtshof", "landesnormen"]
    
    def validate_law_type(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `law_type` value."""

        if slot_value.lower() not in self.law_type_db():
            dispatcher.utter_message(text=f"Derzeit verfügbare Kategorien: Begut, Bundesnormen, Gemeinderecht, Justiz, Landesnormen, Lgbl, Normenliste, RegV, Vfgh, Vwgh")
            return {"law_type": None}

        return {"law_type": slot_value}

