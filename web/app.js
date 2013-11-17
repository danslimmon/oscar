
/**
 * Module dependencies.
 */

var express = require('express');
var routes = require('./routes');
var http = require('http');
var path = require('path');
var doT = require('express-dot');

var oscar_conf = require('./lib/conf').conf;
var trellodb = require('./lib/trellodb').connect();

var app = express();

// all environments
app.set('port', oscar_conf['port'] || 80);
app.set('views', path.join(__dirname, 'views'));

// Use doT instead of jade because jade is too slow
app.set('view engine', 'dot');
app.engine('dot', doT.__express);

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
  trellodb.lookup('learning_opportunities',
                  function(row) {
                    return(row.opp_id == req.params.opp_id)
                  },
                  function(result_rows) {
                    app.locals.opp_data = result_rows[0];
                    next();
                  });
});

app.get('/learn-barcode/:opp_id', routes.learn_barcode);
app.post('/submit-learn-barcode', routes.submit_learn_barcode);

http.createServer(app).listen(app.get('port'), function(){
  console.log('Express server listening on port ' + app.get('port'));
});
