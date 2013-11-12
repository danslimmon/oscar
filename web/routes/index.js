var trellodb = require('../lib/trellodb');

exports.learn_upc = function(req, res){
  res.render('learn_upc', {
    title: 'Oscar: Learn UPC'
  });
};

exports.submit_learn_upc = function(req, res){
  var rule = {upc: req.body['upc'], item: req.body['item']};
  
  req.body['item'];
};
