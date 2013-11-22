import trello
import json


class TrelloDB:
    """Implements a document store on top of Trello."""
    def __init__(self, trello_api, board_id):
        """Initializes the TrelloDB instance.

           'trello_api' should be an instance of trello.TrelloApi, and 'board_id'
           is the ID of the board containing the lists that our DB uses."""
        self._api = trello_api
        self._board_id = board_id

    def _get_list_id(self, table_name):
        """Returns the Trello list ID for a given 'table'."""
        all_lists = self._api.boards.get_list(self._board_id)
        matching_list = [x for x in all_lists if x['name'] == table_name][0]
        return matching_list['id']

    def get_all(self, table_name):
        """Returns all dicts stored in the given table."""
        list_id = self._get_list_id(table_name)
        return [json.loads(card['name']) for card in self._api.lists.get_card(list_id)]

    def insert(self, table_name, item):
        """Inserts the given item (a dict) into the given table."""
        list_id = self._get_list_id(table_name)
        self._api.lists.new_card(list_id, json.dumps(item))
