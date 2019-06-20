import sqlite3
import sys
import db_func

if len(sys.argv) >= 1:
    db_func.db_service_database_path(sys.argv[1])
    db_func.db_service_database_conn_open()
    db_func.db_service_init_tech_tables()


foo = db_func.db_tech_get_all_old_chat_tables_list()
list_old_tables = []
db_func.db_drop_tech()
for table in foo:
     bar = table.split('_')
     db_func.db_service_create_chat_table('-' + bar[1])
     db_func.db_transfer(bar[1])
db_func.db_add_welcomes()