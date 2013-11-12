var Trello = require('node-trello');
var oscar_conf = require('./lib/conf').conf;

var trello_api = new Trello(oscar_conf['trello_app_key'], oscar_conf['trello_token']);

// Turns Trello into a DB.
function TrelloDB() {}

// Returns all items in the given table for which the given callback returns true.
TrelloDB.prototype.lookup = function(table, filter_callback) {
  trello_api.get('1/list/' + opp_list['id'] + '/cards/open', function(err, data) {
    var cards = data;
    var blobs = data.map(function(card) { return card['name'] });
    var rows = blobs.map(function(blob) { return JSON.parse(blob) });
    return rows.filter(filter_callback);
  }
}

// Adds the given item to the given table.
TrelloDB.prototype.insert = function(table, item) {
  trello_api.post('1/list/' + opp_list['id'] + '/cards', function(err, data) {
    var cards = data;
    var blobs = data.map(function(card) { return card['name'] });
    var rows = blobs.map(function(blob) { return JSON.parse(blob) });
    return rows.filter(filter_callback);
  }
}
