#!/usr/local/bin/python3


import mysql.connector, sys, datetime

def getFromUser(prompt, primer):
    print(prompt + " [" + primer + "]")
    tempInput = input()
    if tempInput:
        return tempInput
    else:
        return primer


primeHost     = "localhost"
primeDatabase = ""
primeUser     = "root"
primePassword = ""
primeFilename = "record_count.csv"


host     = getFromUser("host",     primeHost)
database = getFromUser("database", primeDatabase)
user     = getFromUser("user",     primeUser)
password = getFromUser("password", primePassword)
filename = getFromUser("filename", primeFilename)


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

with open(filename, "w") as log:
    for (tableName, tableRows) in cursor:
        print(tableName.ljust(48) + str(tableRows).rjust(6))
        log.write(tableName + "," + str(tableRows) + "\n")

cursor.close()
cnx.close()

