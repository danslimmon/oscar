#!/usr/bin/env python

import time
from datetime import datetime
import struct
import select
import socket
import random
import json
import urllib2
import hashlib
import hmac
import base64

import trello
from twilio.rest import TwilioRestClient

from lib import conf


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


def local_ip():
    """Returns the IP that the local host uses to talk to the Internet."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("trello.com", 80))
    addr = s.getsockname()[0]
    s.close()
    return addr


def generate_opp_id():
    return ''.join(random.sample('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', 12))


def opp_url(opp):
    return 'http://{0}/learn-barcode/{1}'.format(local_ip(), opp['barcode'])


def create_barcode_opp(barcode, trello_api):
    """Creates a learning opportunity for the given barcode and writes it to Trello
    
       Returns the dict."""
    opp = {
        'type': 'barcode',
        'opp_id': generate_opp_id(),
        'barcode': barcode,
        'created_dt': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    rule_lists = trello_api.boards.get_list(conf.get()['trello_db_board'])
    opp_list = [x for x in rule_lists if x['name'] == 'learning_opportunities'][0]
    trello_api.lists.new_card(opp_list['id'], json.dumps(opp))
    return opp


def publish_barcode_opp(opp):
    client = TwilioRestClient(conf.get()['twilio_sid'], conf.get()['twilio_token'])
    message = client.sms.messages.create(body='''Hi! Oscar here. You scanned a code I didn't recognize. Care to fill me in?  {0}'''.format(opp_url(opp)),
                                         to='+{0}'.format(conf.get()['twilio_dest']),
                                         from_='+{0}'.format(conf.get()['twilio_src']))
 

t = trello.TrelloApi(conf.get()['trello_app_key'])
t.set_token(conf.get()['trello_token'])
f = open(conf.get()['scanner_device'], 'rb')
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
    barcode = parse_scanner_data(scanner_data)
    print "Scanned barcode '{0}'".format(barcode)

    # Get the item's description
    u = UPCAPI(conf.get()['digiteyes_app_key'], conf.get()['digiteyes_auth_key'])
    try:
        desc = u.get_description(barcode)
        print "Received description '{0}' for barcode {1}".format(desc, repr(barcode))
    except urllib2.HTTPError, e:
        if 'UPC/EAN code invalid' in e.msg and barcode != '0000':
            # ('0000' is garbage that my scanner occasionally outputs at random)
            print "Barcode {0} not recognized as a UPC; creating learning opportunity".format(repr(barcode))
            opp_id = create_barcode_opp(barcode, t)
            print "Publishing learning opportunity via SMS"
            publish_barcode_opp(opp_id)
            continue
        elif 'Not found' in e.msg:
            print "Barcode {0} not found in UPC database; creating learning opportunity".format(repr(barcode))
            opp_id = create_barcode_opp(barcode, t)
            print "Publishing learning opportunity via SMS"
            publish_barcode_opp(opp_id)
            continue
        else:
            raise
    
    # Match against description rules
    rule_lists = t.boards.get_list(conf.get()['trello_db_board'])
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
    lists = t.boards.get_list(conf.get()['trello_grocery_board'])
    grocery_list = [x for x in lists
                    if x['name'] == conf.get()['trello_grocery_list']][0]
    cards = t.lists.get_card(grocery_list['id'])
    card_names = [card['name'] for card in cards]

    # Add item if it's not there already
    if item_to_add not in card_names:
        print "Adding '{0}' to grocery list".format(item_to_add)
        t.lists.new_card(grocery_list['id'], item_to_add)
