var trellodb = require('../lib/trellodb').connect();
var doT = require('express-dot');

exports.learn_barcode = function(req, res){
//  doT.setGlobals({title: 'Oscar: Learn Barcode'});
  res.render('learn_barcode', {title: 'Oscar: Learn barcode'});
};

exports.submit_learn_barcode = function(req, res){
  var rule = {barcode: req.body['barcode'], item: req.body['item']};

  trellodb.insert('barcode_rules',
                  rule,
                  function() {
                      res.render('thank_barcode', {title: 'Oscar: Learned barcode',
                                                   rule: rule})
                  });
};
