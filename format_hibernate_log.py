#!/usr/local/bin/python3

''' # ---

2017-03-28 22:55

This program takes the console messages and formats them and populates the SQL
queries' values.

It asks for the name of the input file and the name of the file the program
should create as output. The output file will be named [input_file_name].sql
if an output file name is not specified.

An [output_file_name].debug file will be created, as well, listing any debug
(log.debug) messages in the log.

It creates a list of tables that have records affected and writes this to a log
file named by the tablesLogName variable below.

''' # ---


import re, os, sys, time, io


# --


tablesLogName = "tables.log"
tempFileA     = "temp_logA.tmplog"
tempFileB     = "temp_logB.tmplog"
paramCount    = 0
bindings      = []


# --


def cleanPath(pathIn):
  sep = os.path.sep
  if sep == "\\":
    sep = "\\\\" # for windows
  newPath = re.sub(r"[\\/]", sep, pathIn)
  return newPath


def clearBindings():
  bindings[:] = []


def countTableChanges(label, dictionary):
  returnString = ""
  if dictionary:
    for (k,v) in dictionary.items():
      returnString += k.ljust(48) + str(v).rjust(3) + "\n"
  else:
    returnString = "No records " + label
  return returnString


# --


quitPattern = re.compile(r"^(quit|q|stop|exit)$")

foundPattern = re.compile(r"""
  (?:ALL|DEBUG|ERROR|FATAL|INFO|TRACE|WARN)\s+
  .*?\s+-\s+found\s+
  \[(.*?)\]\]?\s+as\s+
  column\s+
  \[([^\]]+)\]
  """, re.VERBOSE)

asPattern = re.compile(r"(?<!\])\s+as\s+([A-z0-9\.\_]+),?")

bindPattern = re.compile(r"binding parameter \[\d+\] as \[.*?\] -(\s(.*))")

multipleParamPattern = re.compile(r"""^\s+\((\? (,\s)?)+ \)""", re.VERBOSE)

multipleBindingPattern = re.compile(r"""^\s+\(((\w+(,\s)?)+) \)""", re.VERBOSE)

paramPattern     = re.compile(r"^\s+(and\s+)?[^\s]+=\?,?$")
newQueryPattern  = re.compile(r"^\s+(insert|select|update|delete\b)")
methodPattern    = re.compile(r"^\+{3} .*$")

logPattern = re.compile(r"""
  ^[-\d\s:,]+
  \[.*?\]\s+
  (?:ALL|DEBUG|ERROR|FATAL|INFO|TRACE|WARN)\s+
  (.*?)\s+-\s+
  (\S.*?)$
  """, re.VERBOSE)

debugPattern = re.compile(r"""
  ^[-\d\s:,]+
  \[.*?\]\s+
  (?:ALL|DEBUG|ERROR|FATAL|INFO|TRACE|WARN)\s+
  hibernate\.SQL\s+-\s*$
  """, re.VERBOSE)

hibernatePattern = re.compile(r"^Hibernate:.*")

throwAwayPattern = re.compile(r"""
  (^\s+values$) |
  (^\s+\((\?(,\s)?)+\)) |
  (\/java\s.*?Dgrails\.home=.*?classpath.*?IntelliJ\sIDEA) |
  (^[-\d\s:,]+\[.*?\]\s
    DEBUG\s+type\.BasicTypeRegistry\s+-\s+Adding\s+type\s+registration.*?->\s+org\.hibernate\.type\..*?Type\@) |
  (^[-\d\s:,]+\[.*?\]\s+
    INFO\s+type\.BasicTypeRegistry\s+-\s+Type\sregistration\s+\[.*?\]\s+overrides\s+previous) |
  (^[-\d\s:,]+\[.*?\]\s+
    TRACE\s+type\.TypeFactory\s+-\s+Scoping\s+types\s+to\s+session\s+factory\s+org\.hibernate\.impl\.SessionFactoryImpl\@) |
  (^\|Configuring\s+classpath$)             |
  (^\|Compiling\s+\d+\s+source\s+files$)    |
  (^\|Packaging\s+Grails\s+application$)    |
  (^\|Running\s+Grails\s+application$)      |
  (^\|Enabling\s+Tomcat\s+NIO\s+connector$) |
  (^Configuring\s+Spring\s+Security\s+(Core|UI)\s+\.+$) |
  (^\.+\s+finished\s+configuring\s+Spring\s+Security\s+(Core|UI)$) |
  (^Testing\s+started\s+at\s+\d+:\d+\s+[AP]M\s+\.+$) |
  (^\.+$) |
  (^\s*$)
  """, re.VERBOSE)


# ---


# Get the path to the log file.
print()
logFilePath = ""
while not os.path.isfile(logFilePath):
  print("Path to log file: ")
  logFilePath = cleanPath(input())
  if quitPattern.search(logFilePath.lower()):
    print("exiting")
    sys.exit()
  if not os.path.isfile(logFilePath):
    print("\nlog file " + logFilePath + " not found\n")


# Get the user's preference on the output file path.
newLogFile = ""
print()
while True:
  print("Output file name:\n(Enter for " + logFilePath + ".sql)")
  newLogFile = cleanPath(input())
  if quitPattern.search(newLogFile.lower()):
    print("exiting")
    sys.exit()
  elif newLogFile is None or newLogFile == "":
    newLogFile = logFilePath + ".sql"
    break
  elif newLogFile.lower() == logFilePath.lower():
    print("\nno. just... no\n")
    time.sleep(1)
    print("you're not even paying attention at this point, are you?")
    time.sleep(1)
    print("(output file name cannot be the same as the input file name)")
    time.sleep(1)
    print("try again...")
    time.sleep(1)
    print()
    continue
  elif os.path.isfile(newLogFile):
    print("file '" + newLogFile + "' already exists")
    print("type 'yes' to overwrite")
    overWriteInput = input().lower()
    if overWriteInput == "yes":
      break
  elif not os.path.exists(os.path.dirname(newLogFile)):
    newPath = os.path.dirname(newLogFile)
    print("the directory '" + newPath + "' doesn't exist.")
    print("create directory path '" + newPath + "'? [y/n]")
    createPathInput = input().lower()
    if createPathInput == "y":
      try:
        os.makedirs(newPath)
        break
      except:
        print("could not create directory path '" + newPath + "'")
        print()
        continue
    else:
      continue


debugFile = newLogFile + ".debug"
debugFileTemp = debugFile + ".tmp"


# ---


# let's go!
print("working...\n")


# ---


# remove duplicate queries
inDebug = False
temp = open(tempFileA, "w", encoding="utf8")
with open(logFilePath, encoding="utf8") as log:
  for line in log:
    if debugPattern.search(line):
      temp.write(line.rstrip() + "\n")
      inDebug = True
    elif hibernatePattern.search(line):
      inDebug = False
    else:
      if inDebug:
        pass
      else:
        temp.write(line.rstrip() + "\n")
temp.close()


# ---


# putting multiline strings on one line
orphan = False
temp = open(tempFileB, "w", encoding="utf8")
with open(tempFileA, encoding="utf8") as log:
  for line in log:
    line = re.sub(r"\[+", "[", line)
    openCount = line.count("[")
    closeCount = line.count("]")
    if orphan:
      if line[0].isalpha() or line[0] == '"' or line[0] == "}":
        temp.write(" ")

    temp.write(line.rstrip())

    if openCount > closeCount:
      orphan = True
    elif openCount < closeCount:
      orphan = False
      temp.write("\n")
    else:
      if not orphan:
        temp.write("\n")
temp.close()


# ---


# Get a dictionary of values found
foundValues = {}
with open(tempFileB, "r", encoding="utf8") as log:
  for line in log:
    if foundPattern.search(line):
      mo = foundPattern.search(line)
      foundValues[mo[2]] = mo[1]


temp = open(tempFileA, "w", encoding="utf8")
with open(tempFileB, "r", encoding="utf8") as log:
  for line in list(log):
    line = re.sub(r"\s{4}", "  ", line)
    temp.write(line)
temp.close()


temp = open(tempFileB, "w", encoding="utf8")
debug = open(debugFileTemp, "w", encoding="utf8")

with open(tempFileA, "r", encoding="utf8") as log:
  lines = reversed(list(log))
  for line in lines:


    # suppressing the lines with the trace results
    if foundPattern.search(line):
      pass


    # here we're replacing placeholders in the queries with the dictionary values from previous pass
    elif asPattern.search(line):
      try:
        temp.write(re.sub(asPattern, " :: " + foundValues[asPattern.search(line)[1]], line.rstrip()) + "\n")

      except:
        # no match found
        temp.write(line.rstrip() + " .. no match ..\n")


    # this line defines a value for a parameter used below
    elif bindPattern.search(line):
      bindingValue = bindPattern.search(line)[2]
      if bindingValue is None or bindingValue == "":
        bindingValue = "''"
      bindings.append(bindingValue)
      paramCount = 0


    elif multipleBindingPattern.search(line):
      matchedVal = multipleBindingPattern.search(line)
      mbCount = len(bindings) - 1
      mbValues = []
      padding = re.search(r"^(\s*)", line).group(1) + "  "
      for binding in re.findall("\w+", line):
        try:
          mbValues.append(binding + " = " + bindings[mbCount])
        except:
          mbValues.append(binding + " = ???")
        mbCount -= 1
      for mbValue in mbValues:
        values = mbValue.split(" = ")
        temp.write(padding + values[0].ljust(30) + " = " + values[1] + "\n")


    # this is a parameter (?) that needs bound to a value from above
    elif paramPattern.search(line):
      try:
        temp.write(line.rstrip() + "    " + bindings[paramCount] + "\n")
      except:
        pass
      paramCount += 1


    # resetting the count of params so the next set of bindings starts at the beginning of the list of bindings
    elif newQueryPattern.search(line):
      paramCount = 0
      temp.write(line.rstrip() + "\n\n")


    elif throwAwayPattern.search(line):
      pass

    elif debugPattern.search(line):
      clearBindings()


    elif methodPattern.search(line):
      temp.write(line.rstrip() + "\n\n\n")
      debug.write("\n" + line.rstrip() + "\n")


    elif logPattern.search(line):
      msg = re.sub(logPattern, logPattern.search(line)[1] + " :: " + logPattern.search(line)[2], line.rstrip() + "\n")
      temp.write(msg)
      debug.write(msg)


    else:
      temp.write(line.rstrip() + '\n')


# ---


# Here we are putting the formatted log file back in the right order.
# Also, we're building a dictionary of the tables that have records added,
# updated, or deleted. The results will be written to the file named by the
# tablesLogName string.

temp.close()
debug.close()

tablesLog      = open(tablesLogName, "w")
tablesUpdated  = {}
tablesDeleted  = {}
tablesInserted = {}
insertSwitch   = False
deleteSwitch   = False
updateSwitch   = False
lineCount      = 0

newLog = open(newLogFile, "w")
with open(tempFileB, "r") as log:
  lines = reversed(list(log))
  for line in lines:
    newLog.write(line.rstrip() + "\n")

    if re.match(r"^\s*insert\s*$", line, re.IGNORECASE):
      (insertSwitch, deleteSwitch, updateSwitch, lineCount) = (True, False, False, 0)
    elif re.match(r"^\s*delete\s*$", line, re.IGNORECASE):
      (insertSwitch, deleteSwitch, updateSwitch, lineCount) = (False, True, False, 0)
    elif re.match(r"^\s*update\s*$", line, re.IGNORECASE):
      (insertSwitch, deleteSwitch, updateSwitch, lineCount) = (False, False, True, 0)
    elif re.match(r"^\s*(\w+)\s*$", line):
      lineCount = lineCount + 1
      table = line.strip()

      if insertSwitch and lineCount == 2:
        insertSwitch = False
        if table in tablesInserted:
          tablesInserted[table] += 1
        else:
          tablesInserted[table] = 1

      if deleteSwitch and lineCount == 2:
        deleteSwitch = False
        if table in tablesDeleted:
          tablesDeleted[table] += 1
        else:
          tablesDeleted[table] = 1

      if updateSwitch and lineCount == 1:
        updateSwitch = False
        if table in tablesUpdated:
          tablesUpdated[table] += 1
        else:
          tablesUpdated[table] = 1

    else:
      lineCount = lineCount + 1


tablesWithInsertedRecords = countTableChanges("inserted", tablesInserted)
tablesWithUpdatedRecords  = countTableChanges("updated",  tablesUpdated)
tablesWithDeletedRecords  = countTableChanges("deleted",  tablesDeleted)

tablesLog.write("""Tables with INSERTED records:

%s


Tables with UPDATED records:

%s


Tables with DELETED records:

%s

""" % (tablesWithInsertedRecords, tablesWithUpdatedRecords, tablesWithDeletedRecords))

newLog.close()
tablesLog.close()


# ---


newDebug = open(debugFile, "w")
with open(debugFileTemp, "r") as debug:
  lines = reversed(list(debug))
  for line in lines:
    newDebug.write(line.rstrip() + "\n")
newDebug.close()


# ---


os.unlink(tempFileA)
os.unlink(tempFileB)
os.unlink(debugFileTemp)


# ---

