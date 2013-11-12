
/**
 * Module dependencies.
 */

var express = require('express');
var routes = require('./routes');
var http = require('http');
var path = require('path');

var oscar_conf = require('./lib/conf').conf;
var trellodb = require('./lib/trellodb');

var app = express();

// all environments
app.set('port', process.env.PORT || 3000);
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'jade');
app.use(express.favicon());
app.use(express.logger('dev'));
app.use(express.json());
app.use(express.urlencoded());
app.use(express.methodOverride());
app.use(app.router);
app.use(express.static(path.join(__dirname, 'public')));

// development only
if ('development' == app.get('env')) {
  app.use(express.errorHandler());
}


app.param('opp_id', function(req, res, next, id) {
  trellodb.get('/1/board/' + oscar_conf['trello_db_board'] + '/lists', function(err, data) {
    var db_lists = data.filter(function(db_list) {return (db_list['name'] == 'learning_opportunities')});
    if (db_lists.length == 0) {
      console.log('Oscar misconfigured; no list named "learning_opportunities"');
      res.send(500, 'Oscar misconfigured; no list named "learning_opportunities"');
      return;
    }
    var opp_list = db_lists[0];

    app.locals.trello_api.get('/1/list/' + opp_list['id'] + '/cards/open', function(err, data) {
      var opps = data.map(function(card) {return JSON.parse(card['name'])});
      opps = opps.filter(function(opp) {return (opp['opp_id'] == req.params.opp_id)});

      if (opps.length == 0) {
        console.log('No learning opportunity with ID "' + id + '"');
        res.send(404, 'No learning opportunity with ID "' + id + '"');
        return;
      }

      app.locals.opp_data = opps[0];
      next();
    });
  });
});

app.get('/learn-upc/:opp_id', routes.learn_upc);
app.post('/submit-learn-upc', routes.submit_learn_upc);

http.createServer(app).listen(app.get('port'), function(){
  console.log('Express server listening on port ' + app.get('port'));
});
