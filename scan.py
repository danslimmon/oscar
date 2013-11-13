#!/usr/bin/env python

import time
import struct
import select
import json
import yaml
import urllib2
import hashlib
import hmac
import base64
import trello


def parse_scanner_data(scanner_data):
    upc_chars = []
    for i in range(0, len(scanner_data), 16):
        chunk = scanner_data[i:i+16]

        # The chunks we care about will match
        # __  __  __  __  __  __  __  __  01  00  __  00  00  00  00  00
        if chunk[8:10] != '\x01\x00' or chunk[11:] != '\x00\x00\x00\x00\x00':
            continue

        digit_int = struct.unpack('>h', chunk[9:11])[0]
        upc_chars.append(str((digit_int - 1) % 10))

    return ''.join(upc_chars)


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
        return json.loads(json_blob)['description']

conf = yaml.load(open('/etc/oscar.yaml').read())


f = open(conf['scanner_device'], 'rb')
while True:
    print 'Waiting for scanner data'

    # Wait for binary data from the scanner and then read it
    scan_complete = False
    scanner_data = ''
    while True:
        rlist, _wlist, _elist = select.select([f], [], [], 0.1)
        if rlist != []:
            new_data = ''
            while not new_data.endswith('\x01\x00\x1c\x00\x01\x00\x00\x00'):
                new_data = rlist[0].read(16)
                scanner_data += new_data
            # There are 4 more keystrokes sent after the one we matched against,
            # so we flush out that buffer before proceeding:
            [rlist[0].read(16) for i in range(4)]
            scan_complete = True
        if scan_complete:
            break
 
    # Parse the binary data as a UPC
    upc = parse_scanner_data(scanner_data)

    # Get the item's description
    u = UPCAPI(conf['digiteyes_app_key'], conf['digiteyes_auth_key'])
    desc = u.get_description(upc)

    # Match against description rules
    t = trello.TrelloApi(conf['trello_app_key'])
    t.set_token(conf['trello_token'])
    rule_lists = t.boards.get_list(conf['trello_db_board'])
    desc_rule_list = [x for x in rule_lists
                      if x['name'] == 'description_rules'][0]
    desc_rules = [json.loads(card['name']) for card in t.lists.get_card(desc_rule_list['id'])]
    item_to_add = None
    for r in desc_rules:
        if r['search_term'].lower() in desc.lower():
            item_to_add = r['item']
    if item_to_add is None:
        print "Don't know what to add for description '{0}'".format(desc)
        continue

    # Get the current grocery list
    lists = t.boards.get_list(conf['trello_grocery_board'])
    grocery_list = [x for x in lists
                    if x['name'] == conf['trello_grocery_list']][0]
    cards = t.lists.get_card(grocery_list['id'])
    card_names = [card['name'] for card in cards]

    # Add item if it's not there already
    if item_to_add not in card_names:
        t.lists.new_card(grocery_list['id'], item_to_add)
