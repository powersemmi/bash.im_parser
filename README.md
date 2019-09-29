# bash.im_parser
The script to parce bash.im
## Requirements
python3.7 or later

sqlite3 database with table from db.sql file
### using libs:
  * requests
  * sqlite3
  * multiprocessing
  * lxml
  * datetimee
  * sys
  * os


## How to use


1) Enter ```./bash.im_parser.py init path_to_sqlite_database``` if you want to initialize the parser and start parsing
2) Enter ```./bash.im_parser.py update path_to_sqlite_database``` if you want update parsed data
