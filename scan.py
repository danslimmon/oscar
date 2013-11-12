#!/usr/bin/env python

import json
import yaml
import urllib2
import hashlib
import hmac
import base64
import trello


class UPCAPI:
    BASEURL = 'https://www.digit-eyes.com/gtin/v2_0'

    def __init__(self, app_key, auth_key):
        self._app_key = app_key
        self._auth_key = auth_key

    def _signature(self, upc):
        h = hmac.new(self._auth_key, upc, hashlib.sha1)
        return base64.b64encode(h.digest())

    def _url(self, upc):
        return '{0}/?upcCode={1}&field_names=description&language=en&app_key={2}&signature={3}'.format(
            self.BASEURL, upc, self._app_key, self._signature(upc))

    def get_description(self, upc):
        """Returns the product description for the given UPC.
        
           `upc`: A string containing the UPC."""
        url = self._url(upc)
        json_blob = urllib2.urlopen(url).read()
        #json_blob = '{"description" :"Peets Coffee Coffee Whole Bean, Deep Roast, House Blend","upc_code":"785357100527"}'
        return json.loads(json_blob)['description']

conf = yaml.load(open('/etc/oscar.yaml').read())

# Get the item's description
u = UPCAPI(conf['digiteyes_app_key'], conf['digiteyes_auth_key'])
desc = u.get_description("785357100527")

# Match against description rules
t = trello.TrelloApi(conf['trello_app_key'])
t.set_token(conf['trello_token'])
rule_lists = t.boards.get_list(conf['trello_rule_board'])
desc_rule_list = [x for x in rule_lists
                  if x['name'] == 'description_rules'][0]
desc_rules = [json.loads(card['name']) for card in t.lists.get_card(desc_rule_list['id'])]
item_to_add = None
for r in desc_rules:
    if r['search_term'].lower() in desc.lower():
        item_to_add = r['item']

# Get the current grocery list
lists = t.boards.get_list(conf['trello_grocery_board'])
grocery_list = [x for x in lists
                if x['name'] == conf['trello_grocery_list']][0]
cards = t.lists.get_card(grocery_list['id'])
card_names = [card['name'] for card in cards]

# Add item if it's not there already
if item_to_add not in card_names:
    t.lists.new_card(grocery_list['id'], item_to_add)
