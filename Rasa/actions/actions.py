# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from elasticsearch import Elasticsearch   

import requests
from rasa_sdk.events import SlotSet, FollowupAction
from rasa_sdk.forms import FormAction

class ActionLawRespond(Action):

    def name(self) -> Text:
        return "action_law_respond"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        search_text = tracker.latest_message.get("text")
        es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

        body = {
            "_source": "law",
            "size": 3,
            "query": {
                "match_phrase": {
                    "law": '"' + search_text + '"'
                }
            }
        }

        result = es.search(index='console_law', body=body)

        dispatcher.utter_message(result['hits']['hits'][0]['_source']['law'])

        return []

class LawsearchForm(FormAction):
    """Custom form action to fill all slots required to find specific type
    of healthcare facilities in a certain city or zip code."""

    def name(self) -> Text:
        """Unique identifier of the form"""

        return "lawsearch_form"

    def submit(self,
               dispatcher: CollectingDispatcher,
               tracker: Tracker,
               domain: Dict[Text, Any]
               ) -> List[Dict]:
        """Once required slots are filled, print buttons for found facilities"""

        search_text = tracker.get_slot('law_keyword')

        es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

        body = {
            "_source": "law",
            "size": 3,
            "query": {
                "match_phrase": {
                    "law": '"' + search_text + '"'
                }
            }
        }

        result = es.search(index='console_law', body=body)

        dispatcher.utter_message("halimali lefutott am")

        return []