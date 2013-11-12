var yaml = require('js-yaml');
var fs = require('fs');

exports.conf = yaml.load(fs.readFileSync('/etc/oscar.yaml', encoding='utf-8'));
