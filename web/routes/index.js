var trellodb = require('../lib/trellodb');

exports.learn_barcode = function(req, res){
  res.render('learn_barcode', {
    title: 'Oscar: Learn Barcode'
  });
};

exports.submit_learn_barcode = function(req, res){
  var rule = {barcode: req.body['upc'], item: req.body['item']};
  
  req.body['item'];
};
