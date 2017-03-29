#!/usr/local/bin/python3

''' # ---

mysql_record_count.py

This program asks for connection information for a database and a desired
output comma-separated values filename. Then it connects to the database -- if
it can -- and creates the output file which is a list of tables with the count
of records in each table.

In testing, run this before triggering the action you are wanting to test, then
run it again after triggering the action. Save the two executions as two
different files. Then compare the two (with compare_reconrd_counts.py is easy).

''' # ---


import mysql.connector, sys, datetime


def getFromUser(prompt, primer):
    print(prompt + " [" + primer + "]")
    tempInput = input()
    if tempInput:
        return tempInput
    else:
        return primer

# defaults that can be overridden by the user
primeHost     = "localhost"
primeDatabase = ""
primeUser     = "root"
primePassword = ""
primeFilename = "record_count.csv"


# give user opportunity to override defaults
host     = getFromUser("host",     primeHost)
database = getFromUser("database", primeDatabase)
user     = getFromUser("user",     primeUser)
password = getFromUser("password", primePassword)
filename = getFromUser("filename", primeFilename)


# attempt database connection
cnx = None
try:
    cnx = mysql.connector.connect(
        host     = host,
        database = database,
        user     = user,
        password = password)
except:
    errorMessage = """

Connection failed with the following:

    host:      {0}
    database:  {1}
    username:  {2}
    password:  {3}

"""
    print(errorMessage.format(host, database, user, password))
    sys.exit()


cursor = cnx.cursor(buffered=True)

query = "SELECT TABLE_NAME, TABLE_ROWS FROM `information_schema`.`tables` where `table_schema` = '" + database + "'"

cursor.execute(query)


# write the results to the output file
with open(filename, "w") as log:
    for (tableName, tableRows) in cursor:
        print(tableName.ljust(48) + str(tableRows).rjust(6))
        log.write(tableName + "," + str(tableRows) + "\n")

cursor.close()
cnx.close()


# the end
# ---

