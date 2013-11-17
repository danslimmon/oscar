var trellodb = require('../lib/trellodb').connect();

exports.learn_barcode = function(req, res){
  res.render('learn_barcode', {
    title: 'Oscar: Learn Barcode'
  });
};

exports.submit_learn_barcode = function(req, res){
  var rule = {barcode: req.body['barcode'], item: req.body['item']};

  trellodb.insert('barcode_rules',
                  rule,
                  function() {
                      res.render('thank_barcode', {'rule': rule})
                  });
 
  req.body['item'];
};
