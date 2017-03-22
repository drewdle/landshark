#!/usr/local/bin/python3


import re, os, sys, time, io


def cleanPath( pathIn ):
  sep = os.path.sep
  if sep == '\\':
    sep = '\\\\'
  newPath = re.sub( r'[\\/]', sep, pathIn )
  return newPath


def clearBindings():
  bindings[:] = []


logFilePath = ''
newLogFile  = ''
tempFileA   = 'temp_logA.tmplog'
tempFileB   = 'temp_logB.tmplog'
paramCount  = 0
bindings    = []


quitPattern = re.compile( r'^(quit|q|stop|exit)$' )


# Get the path to the log file.
print()
while not os.path.isfile( logFilePath ):
  print( 'Path to log file: ' )
  logFilePath = cleanPath(input())
  if quitPattern.search( logFilePath.lower() ):
    print( 'exiting' )
    sys.exit()
  if not os.path.isfile(logFilePath):
    print( '\nlog file ' + logFilePath + ' not found\n' )


# Get the user's preference on the output file path.
print()
goodNewLogFilePath = False
while not goodNewLogFilePath:
  print( 'Output file name:\n(Enter for ' + logFilePath + '.sql)' )
  newLogFile = cleanPath(input())
  if quitPattern.search(newLogFile.lower()):
    print( 'exiting' )
    sys.exit()
  elif newLogFile is None or newLogFile == '':
    newLogFile = logFilePath + '.sql'
    break
  elif newLogFile.lower() == logFilePath.lower():
    print( '\nno. just... no\n' )
    time.sleep(1)
    print( 'you\'re not even paying attention at this point, are you?' )
    time.sleep(1)
    print( '(output file name cannot be the same as the input file name)' )
    time.sleep(1)
    print( 'try again...' )
    time.sleep(1)
    print()
    continue
  elif os.path.isfile( newLogFile ):
    print( 'file "' + newLogFile + '" already exists' )
    print( 'type "yes" to overwrite' )
    overWriteInput = input().lower()
    if overWriteInput == 'yes':
      break
  elif not os.path.exists( os.path.dirname(newLogFile) ):
    newPath = os.path.dirname( newLogFile )
    print( "the directory '" + newPath + "' doesn't exist." )
    print( 'create directory path "' + newPath + '"? [y/n]' )
    createPathInput = input().lower()
    if createPathInput == 'y':
      try:
        os.makedirs( newPath )
        break
      except:
        print( 'could not create directory path "' + newPath + '"' )
        print()
        continue
    else:
      continue


# let's go!
print( 'working...\n' )

# 2017-02-27 10:38:27,012 [http-nio-8080-exec-8] TRACE sql.BasicExtractor  - found [true] as column [account3_69_0_]
foundPattern = re.compile( r'TRACE\s+.*?found\s+\[(.*?)\]\s+as\s+column\s+\[(.*?)\]' )

# found [1139] as column [owner26_58_0_]
# found [Because there are no other funding sources associated with this transaction, these exhibits are Not Applicable] as column [formula4_0_]


# 2017-02-27 10:38:27,012 [http-nio-8080-exec-8] TRACE sql.BasicExtractor  - found [false] as column [account4_69_0_]
asPattern = re.compile( r'(?<!\])\s+as\s+([A-z0-9\.\_]+),?' )

# 2017-02-27 10:38:27,011 [http-nio-8080-exec-8] TRACE sql.BasicBinder  - binding parameter [1] as [BIGINT] - 1070
bindPattern = re.compile( r'binding parameter \[\d+\] as \[.*?\] -(\s(.*))' )

multipleParamPattern = re.compile( r'''^\s+\( (\? (,\s)?)+ \)''', re.VERBOSE )

multipleBindingPattern = re.compile( r'''^\s+\( ((\w+(,\s)?)+) \)''', re.VERBOSE )

paramPattern     = re.compile( r'^\s+(and\s+)?[^\s]+=\?,?$' )
newQueryPattern  = re.compile( r'^\s+(insert|select|update|delete\b)' )
methodPattern    = re.compile( r'^\+{3} .*$' )

# 2017-03-08 14:01:02,324 [http-nio-8080-exec-3] DEBUG hibernate.SQL  -
debugPattern = re.compile( r'^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2},\d+\s\[.*?\]\s(ALL|DEBUG|ERROR|FATAL|INFO|TRACE|WARN)\shibernate\.SQL\s+-\s*$' )
hibernatePattern = re.compile( r'^Hibernate:.*' )

throwAwayPattern = re.compile( r'''
  (^\s+values$) |
  (^\s+\((\?(,\s)?)+\)) |
  (\/java\s.*?Dgrails\.home=.*?classpath.*?IntelliJ\sIDEA) |
  (^[-\d\s:,]+\[.*?\]\s
    DEBUG\s+type\.BasicTypeRegistry\s+-\s+Adding\s+type\s+registration.*?->\s+org\.hibernate\.type\..*?Type\@
  ) |
  (^[-\d\s:,]+\[.*?\]\s+
    INFO\s+type\.BasicTypeRegistry\s+-\s+Type\sregistration\s+\[.*?\]\s+overrides\s+previous
  ) |
  (^[-\d\s:,]+\[.*?\]\s+
    TRACE\s+type\.TypeFactory\s+-\s+Scoping\s+types\s+to\s+session\s+factory\s+org\.hibernate\.impl\.SessionFactoryImpl\@
  ) |
  (^\|Configuring\s+classpath$)             |
  (^\|Compiling\s+\d+\s+source\s+files$)    |
  (^\|Packaging\s+Grails\s+application$)    |
  (^\|Running\s+Grails\s+application$)      |
  (^\|Enabling\s+Tomcat\s+NIO\s+connector$) |
  (^Configuring\s+Spring\s+Security\s+(Core|UI)\s+\.+$) |
  (^\.+\s+finished\s+configuring\s+Spring\s+Security\s+(Core|UI)$) |
  (^Testing\s+started\s+at\s+\d+:\d+\s+[AP]M\s+\.+$) |
  (^\.+$)
  ''', re.VERBOSE )


# remove duplicate queries
inDebug = False
temp = open( tempFileA, 'w', encoding='utf8' )
with open( logFilePath, encoding='utf8' ) as log:
  for line in log:
    if debugPattern.search( line ):
      temp.write( line.rstrip() + '\n' )
      inDebug = True
    elif hibernatePattern.search( line ):
      inDebug = False
    else:
      if inDebug:
        pass
      else:
        temp.write( line.rstrip() + '\n' )
temp.close()

# putting multiline strings on one line
orphan = False
temp = open( tempFileB, 'w', encoding='utf8' )
with open( tempFileA, encoding='utf8' ) as log:
  for line in log:
    openCount = line.count('[')
    closeCount = line.count(']')
    if orphan:
      if line[0].isalpha() or line[0] == '"' or line[0] == '}':
        temp.write( ' ' )

    temp.write( line.rstrip() )

    if openCount > closeCount:
      orphan = True
    elif openCount < closeCount:
      orphan = False
      temp.write( '\n' )
    else:
      if not orphan:
        temp.write( '\n' )
temp.close()


# Get a dictionary of values found
foundValues = {}
with open( tempFileB, 'r', encoding='utf8' ) as log:
  for line in log:
    if foundPattern.search(line):
      mo = foundPattern.search(line)
      foundValues[mo[2]] = mo[1]


temp = open( tempFileA, 'w', encoding='utf8' )
with open( tempFileB, 'r', encoding='utf8' ) as log:
  for line in list(log):
    line = re.sub( r'\s{4}', '  ', line )
    temp.write( line )
temp.close()


temp = open( tempFileB, 'w', encoding='utf8' )
with open( tempFileA, 'r', encoding='utf8' ) as log:
  lines = reversed( list( log ))
  for line in lines:


    # suppressing the lines with the trace results
    if foundPattern.search(line):
      pass


    # here we're replacing placeholders in the queries with the dictionary values from previous pass
    elif asPattern.search(line):
      try:
        pass
        temp.write( re.sub( asPattern, ' :: ' + foundValues[asPattern.search(line)[1]], line.rstrip()) + '\n' )

      except:
        # no match found
        temp.write( line.rstrip() + ' .. no match ..\n' )


    # this line defines a value for a parameter used below
    elif bindPattern.search(line):
      bindingValue = bindPattern.search(line)[2]
      if bindingValue is None or bindingValue == '':
        bindingValue = "''"
      bindings.append( bindingValue )
      paramCount = 0


    elif multipleBindingPattern.search(line):
      matchedVal = multipleBindingPattern.search(line)
      mbCount = len(bindings) - 1
      mbValues = []
      padding = re.search( r'^(\s*)', line ).group(1) + '  '
      for binding in re.findall( '\w+', line ):
        try:
          mbValues.append( binding + ' = ' + bindings[mbCount] )
        except:
          mbValues.append( binding + ' = ???' )
        mbCount -= 1
      for mbValue in mbValues:
        values = mbValue.split( ' = ' )
        temp.write( padding + values[0].ljust( 30 ) + ' = ' + values[1] + '\n' )


    # this is a parameter (?) that needs bound to a value from above
    elif paramPattern.search(line):
      try:
        temp.write( line.rstrip() + '    ' + bindings[paramCount] + '\n' )
      except:
        pass
      paramCount += 1


    # resetting the count of params so the next set of bindings starts at the beginning of the list of bindings
    elif newQueryPattern.search(line):
      paramCount = 0
      temp.write( line.rstrip() + '\n\n' )


    elif throwAwayPattern.search(line):
      pass


    elif debugPattern.search(line):
      clearBindings()


    elif methodPattern.search(line):
      temp.write( line.rstrip() + '\n\n\n' )


    else:
      temp.write( line.rstrip() + '\n' )

temp.close()


newLog = open( newLogFile, 'w' )
with open( tempFileB, 'r' ) as log:
  lines = reversed(list(log))
  for line in lines:
    newLog.write( line )
newLog.close()

os.unlink( tempFileA )
os.unlink( tempFileB )


