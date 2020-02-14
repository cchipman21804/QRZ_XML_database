import urllib.request
import getpass
from os import path
import csv
import datetime

# v1.01
# Logs into QRZ XML Database Server
# Parses xml data for session key, server messages, and requested data
# Displays all server messages on console
# Displays all data fields on console
# Saves all data fields to a CSV formatted file

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

# from https://www.qrz.com/XML/current_spec.html
# QRZ's top-level node is the <QRZDatabase> element. All responses from the QRZ server are prefaced with this
# element. Three child node types are defined for this level. They are:
# <Session>
# <Callsign>
# <DXCC>

# If the username and password are accepted (from a subscriber), the system will respond with:

# <?xml version="1.0" ?>
# <QRZDatabase version="1.33">
#  <Session>
#    <Key>2331uf894c4bd29f3923f3bacf02c532d7bd9</Key>
#    <Count>123</Count>
#    <SubExp>Wed Jan 1 12:34:03 2013</SubExp>
#    <GMTime>Sun Aug 16 03:51:47 2012</GMTime>
#  </Session>
# </QRZDatabase>

# If the username and password are accepted (from a NON-subscriber), the system will respond with:

# <?xml version="1.0" encoding="utf-8" ?>
# <QRZDatabase version="1.24" xmlns="http://xmldata.qrz.com">
# <Session>
# <Key>bfebb4159a07f84b2e988ab59192e4d5</Key>
# <Count>7</Count>
# <SubExp>non-subscriber</SubExp>
# <GMTime>Thu Jan 16 18:28:18 2020</GMTime>
# <Remark>cpu: 0.023s</Remark>
# </Session>
# </QRZDatabase>

# Session keys are dynamically managed by the server and have no guaranteed lifetime. When a session key expires or
# becomes invalidated, a new key may be issued upon request. Client programs should cache all session keys provided by
# the server and reuse them until they expire. This practice maximizes client performance and serves to minimize the
# load on QRZ's servers.

# As a general programming pattern, clients should expect to perform only one login operation per session. The session
# key returned from a successful login should then be locally cached and reused as many times as possible. All clients
# should monitor the status response returned in each transaction and be prepared to login again whenever indicated.

# A session key is valid only for a single user and may become immediately invalidated if it is detected that the
# user's IP address or other identifying information changes after login has been completed. The interface does not
# use HTTP cookies, Javascript, or HTML.

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

# QRZ Database Header Labels:
# These are the same as the XML tags in the database specifications, except where they clash with Python reserved words.

# qrz_fields = ("call", "xref", "aliases", "dxcc", "fname", "name", "addr1", "addr2", "state", "zip", "country", "ccode",
#              "lat", "lon", "grid", "county", "fips", "land", "efdate", "expdate", "p_call", "license class",
#              "license codes", "qslmgr", "email", "url", "u_views", "bio", "biodate", "image", "imageinfo", "serial",
#              "moddate","MSA", "AreaCode", "TimeZone", "GMTOffset", "DST", "eqsl", "mqsl", "cqzone", "ituzone", "born",
#              "user", "lotw", "iota", "geoloc")

qrz_fields = ("Callsign", "Cross Reference", "Aliases", "DXCC Entity ID", "First Name", "Last Name", "Address", "City",
              "State", "ZIP", "Country", "DXCC Entity Code", "Latitude", "Longitude", "Grid Square Locator", "County",
              "FIPS County Identifier", "DXCC Country Name", "License Effective Date", "License Expiration Date",
              "Previous Callsign", "License Class", "License Codes", "QSL Manager", "Email Address", "QRZ webpage URL",
              "QRZ webpage views", "Bio HTML Length (bytes)", "Last Bio Update", "Image URL",
              "Image Specs (height:width:bytes", "QRZ serial #", "QRZ Record Last Modified", "Metro Service Area",
              "Area Code", "Time Zone", "GMT Offset", "Observes Daylight Savings Time", "Accepts eQSL",
              "Returns paper QSL", "CQ Zone Identifier", "ITU Zone Identifier", "Operator's Year of Birth",
              "QRZ Record Manager", "Accepts LOTW", "IOTA Designator", "Source of Lat/Long data")

# Initialize record fields with header labels & write header record to file
# Specify header label order
call = qrz_fields[0]  # callsign
xref = qrz_fields[1]  # Cross reference: the query callsign that returned this record
aliases = qrz_fields[2]  # Other callsigns that resolve to this record
dxcc = qrz_fields[3]  # DXCC entity ID (country code for the callsign
fname = qrz_fields[4]  # first name
name = qrz_fields[5]  # last name
addr1 = qrz_fields[6]  # address line 1 (i.e. house # and street)
addr2 = qrz_fields[7]  # address line 2 (i.e. city name)
state = qrz_fields[8]  # state (USA only)
zip = qrz_fields[9]  # Zip/postal code
country = qrz_fields[10]  # country name for the QSL mailing address
ccode = qrz_fields[11]  # DXCC entity code for the mailing address country
lat = qrz_fields[12]  # latitude of address (signed decimal) S < 0 > N
lon = qrz_fields[13]  # longitude of address (signed decimal) W < 0 > E
grid = qrz_fields[14]  # grid locator
county = qrz_fields[15]  # county name (USA)
fips = qrz_fields[16]  # FIPS county identifier (USA)
land = qrz_fields[17]  # DXCC country name of the callsign
efdate = qrz_fields[18]  # license effective date (USA)
expdate = qrz_fields[19]  # license expiration date (USA)
p_call = qrz_fields[20]  # previous callsign
license_class = qrz_fields[21]  # "<class>" license class
license_codes = qrz_fields[22]  # "<codes>" license type codes (USA)
qslmgr = qrz_fields[23]  # QSL manager info
email = qrz_fields[24]  # email address
qrz_webpage_addr = qrz_fields[25]  # web page address
u_views = qrz_fields[26]  # QRZ web page views
bio = qrz_fields[27]  # approximate length of the bio HTML in bytes
biodate = qrz_fields[28]  # date of the last bio update
image = qrz_fields[29]  # full URL of the callsign's primary image
imageinfo = qrz_fields[30]  # height:width:size in bytes, of the image file
serial = qrz_fields[31]  # QRZ database serial number
moddate = qrz_fields[32]  # QRZ callsign last modified date
MSA = qrz_fields[33]  # Metro Service Area (USPS)
AreaCode = qrz_fields[34]  # Telephone Area Code (USA)
TimeZone = qrz_fields[35]  # Time Zone (USA)
GMTOffset = qrz_fields[36]  # GMT Time Offset
DST = qrz_fields[37]  # Daylight Savings Time Observed
eqsl = qrz_fields[38]  # Will accept e-qsl (0/1 or blank if unknown)
mqsl = qrz_fields[39]  # Will return paper QSL (0/1 or blank if unknown)
cqzone = qrz_fields[40]  # CQ Zone identifier
ituzone = qrz_fields[41]  # ITU Zone identifier
born = qrz_fields[42]  # operator's year of birth
user = qrz_fields[43]  # User who manages this callsign on QRZ
lotw = qrz_fields[44]  # Will accept LOTW (0/1 or blank if unknown)
iota = qrz_fields[45]  # IOTA Designator (blank if unknown)
geoloc = qrz_fields[46]  # Describes source of lat/long data

# qrz_fields = ("call", "xref", "aliases", "dxcc", "fname", "name", "addr1", "addr2", "state", "zip", "country", "ccode",
#              "lat", "lon", "grid", "county", "fips", "land", "efdate", "expdate", "p_call", "license class",
#              "license codes", "qslmgr", "email", "url", "u_views", "bio", "biodate", "image", "imageinfo", "serial",
#              "moddate","MSA", "AreaCode", "TimeZone", "GMTOffset", "DST", "eqsl", "mqsl", "cqzone", "ituzone", "born",
#              "user", "lotw", "iota", "geoloc")

qrz_record = [call, xref, aliases, dxcc, fname, name, addr1, addr2, state, zip, country, ccode, lat, lon, grid, county,
              fips, land, efdate, expdate, p_call, license_class, license_codes, qslmgr, email, qrz_webpage_addr,
              u_views, bio, biodate, image, imageinfo, serial, moddate, MSA, AreaCode, TimeZone, GMTOffset, DST, eqsl,
              mqsl, cqzone, ituzone, born, user, lotw, iota, geoloc]

servername = "QRZ Database XML Server"
csvfilename = "_emails.csv"
keyfilename = "qrz.key"
callsfilename = "_callsigns.txt"
xmlsessionfile = ""
key = ""

# loginxmlurl = 'http://www.qrz.com/dxml/xml.pl' -- this URL (from C# source code of QRZXMLReference)
# Using this URL results in HTTP Error 404: Not Found

loginxmlurl = 'http://xmldata.qrz.com/xml/'  # -- updated URL from https://www.qrz.com/page/current_spec.html

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
# *                                                                 *
# *                          Functions                              *
# *                                                                 *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

def qrzlogin():
    username = input("Login with your QRZ username: ")

    # SECURITY WARNING!!! This Python script may display your QRZ password in PLAIN TEXT on the console!!!
    print("\n!!!SECURITY WARNING!!! This Python script may display your QRZ password in PLAIN TEXT on the console!!!")
    print("\n!!!SECURITY WARNING!!! This Python script sends your QRZ password in PLAIN TEXT over an <! UNSECURE !>")
    print("Hypertext Transfer Protocol (http) Internet connection!!!  If you are uncomfortable with this, please")
    print("enter \"quit\" at the password prompt to immediately exit.\n")

    password = getpass.getpass("Enter your QRZ password: ")

    if password == "quit": exit()

    # SECURITY WARNING!!! This Python script sends your QRZ password in PLAIN TEXT over an http connection!!!
    url = loginxmlurl + "?username=" + username + ";password=" + password

    return url

def getxml(url):
    # Log in to QRZ Database XML server:
    req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req)
    respdata = resp.read()
    # print("\nCaptured XML is " + str(len(respData)) + " bytes long.")
    # print(respData)
    xmlsessionfile = str(respdata)
    return xmlsessionfile

def parsexml(tag,xml):
    # Look for two occurrences of tag in xmlsessionfile (string)
    # Place contents between tags into msg

    # Find opening ('<' + tag) - tag already contains the closing '>'
    startidx = xml.find('<' + tag) + len('<' + tag)

    # Find ending ('</' + tag)
    endidx = xml.find('</' + tag)

#    print("Start index: " + str(startidx))
#    print("End index: " + str(endidx))
#    print(xml[startidx:endidx])

    return startidx, endidx

def instructions():
    print("\nThis program repeatedly polls the {} with a list of amateur radio callsigns".format(servername))
    print("stored in the text file - {}. The contents of each record are displayed on the console as they are "
          .format(callsfilename))
    print("accessed in real time. If the record contains an email address field, that record is added to the contents")
    print("of the text file - {}. The contents of {} can be imported later to an Excel spreadsheet as a Comma "
          .format(csvfilename,csvfilename))
    print("Separated Values (.CSV) file. If you need a new file, delete the existing {} so this program can create"
          .format(csvfilename))
    print("a new one.")
    print("This program will end if the {} returns any errors - i.e. \"not found\" or \"Session Timeout\".\n"
          .format(servername))
    print("*** If a record is not found in the {}:".format(servername))
    print("    1> Open {} in a text editor.".format(callsfilename))
    print("    2> Remove the callsign that triggered the error AND ALL PREVIOUS CALLSIGNS IN THE LIST.")
    print("    3> Save {} and restart this program.\n".format(callsfilename))
    print("*** If the {} returns the error \"Session Timeout\":".format(servername))
    print("    1> Delete the text file {} and restart this program.".format(keyfilename))
    print("       The program will not find {} and ask you for your QRZ login credentials.")
    print("       After it logs into {}, you should be given a new session key, and this program will save it in {}\n"
          .format(servername,keyfilename))
    return
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
# *                                                                 *
# *                             Main                                *
# *                                                                 *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

error = 0

# Error codes are binary in nature
# Bit 3 indicates that the callsign input text file does not exist - this is grounds for immediate program termination.
# Bit 2 indicates no Session Key returned from server - program needs a session key to access the server
# Bit 1 indicates an error message from the server - program terminates so user can handle it
# Bit 0 indicates no response from QRZ server - this is grounds for immediate program termination.

print("\nQRZ CALL SIGN SEARCH v1.01")
instructions()
prompt = input("Enter 'y' if you are ready to proceed or any other key to exit...")
prompt = prompt.lower()
if prompt != 'y': exit(error)

# If callsign TXT file does not exist, exit & report error
if not path.exists(callsfilename):
    print("*** ERROR 4 -- Callsign input TXT file does not exist...")
    print("Create the file and place it in the working directory.")
    error += 8  # Set error code bit 3
    exit(error)  # Exit the program immediately.  This program cannot work without this data file.

# If CSV file does not exist, create it & write the header record
if not path.exists(csvfilename):
    print("*** CSV file does not exist...creating new file...")
    # Open csv formatted file - 'w'rite csv as 'b'inary
    csvFile = open(csvfilename, 'w', newline='')
    writer = csv.writer(csvFile)

    # Create CSV header record from QRZ XML Database fields
# qrz_record = [call, email, xref, aliases, p_call,
#                   fname, name, addr1, addr2, state, zip, county, efdate,
#                   expdate, license_class]

    # Tried this because the statements below are tedious
#    writer.writerow(qrz_record)

    writer.writerow([call, xref, aliases, dxcc, fname, name, addr1, addr2, state, zip, country, ccode, lat, lon, grid,
                     county, fips, land, efdate, expdate, p_call, license_class, license_codes, qslmgr, email,
                     qrz_webpage_addr, u_views, bio, biodate, image, imageinfo, serial, moddate, MSA, AreaCode,
                     TimeZone, GMTOffset, DST, eqsl, mqsl, cqzone, ituzone, born, user, lotw, iota, geoloc])

    # Close the file
    csvFile.close()

# Unsuccessful attempt to clear record fields of header strings
# for field in range(0,len(qrz_record)): qrz_record[field] = ""

# This does not work because each item in the qrz_record list is assigned its value by those variables.
# This does not clear the individual variable. It only clears the values in the list.
# This is the result in the CSV file:
# (header record):  call,xref,aliases,dxcc,fname,name,addr1,addr2,state,zip,country,ccode,lat,lon,grid,county,fips,...
# (queried record): KB1EJH,xref,aliases,291,Carl,Davis,PO BOX 180,Georgetown,DE,19947-0180,United States,271,...
# (desired record): KB1EJH,,,291,Carl,Davis,PO BOX 180,Georgetown,DE,19947-0180,United States,271,38.691139,...

# Clear record fields of header strings (the tedious way)
call = ""
xref = ""
aliases = ""
dxcc = ""
fname = ""
name = ""
addr1 = ""
addr2 = ""
state = ""
zip = ""
country = ""  # qrz_fields[10]
ccode = ""  # qrz_fields[11]
lat = ""  # qrz_fields[12]
lon = ""  # qrz_fields[13]
grid = ""  # qrz_fields[14]
county = ""  # qrz_fields[15]
fips = ""  # qrz_fields[16]
land = ""  # qrz_fields[17]
efdate = ""  # qrz_fields[18]
expdate = ""  # qrz_fields[19]
p_call = ""  # qrz_fields[20]
license_class = ""  # qrz_fields[21]
license_codes = ""  # qrz_fields[22]
qslmgr = ""  # qrz_fields[23]
email = ""  # qrz_fields[24]
qrz_webpage_addr = ""  # qrz_fields[25] # web page address
u_views = ""  # qrz_fields[26] # QRZ web page views
bio = ""  # qrz_fields[27] # approximate length of the bio HTML in bytes
biodate = ""  # qrz_fields[28] # date of the last bio update
image = ""  # qrz_fields[29] # full URL of the callsign's primary image
imageinfo = ""  # qrz_fields[30] # height:width:size in bytes, of the image file
serial = ""  # qrz_fields[31] # QRZ database serial number
moddate = ""  # qrz_fields[32] # QRZ callsign last modified date
MSA = ""  # qrz_fields[33] # Metro Service Area (USPS)
AreaCode = ""  # qrz_fields[34] # Telephone Area Code (USA)
TimeZone = ""  # qrzfields[35] # Time Zone (USA)
GMTOffset = ""  # qrz_fields[36] # GMT Time Offset
DST = ""  # qrz_fields[37] # Daylight Savings Time Observed
eqsl = ""  # qrz_fields[38] # Will accept e-qsl (0/1 or blank if unknown)
mqsl = ""  # qrz_fields[39] # Will return paper QSL (0/1 or blank if unknown)
cqzone = ""  # qrz_fields[40] # CQ Zone identifier
ituzone = ""  # qrz_fields[41] # ITU Zone identifier
born = ""  # qrz_fields[42] # operator's year of birth
user = ""  # qrz_fields[43] # User who manages this callsign on QRZ
lotw = ""  # qrz_fields[44] # Will accept LOTW (0/1 or blank if unknown)
iota = ""  # qrz_fields[45] # IOTA Designator (blank if unknown)
geoloc = ""  # qrz_fields[46] # Describes source of lat/long data

print("*** Checking for saved session key...")

if not path.exists(keyfilename):
    print("*** Session key file not found...")

    # Login and get a new session key

    url = qrzlogin()
    xmlsessionfile = getxml(url)

    print("\n")
    # print(xmlsessionfile) # Uncomment this statement for debugging purposes

    # Parse login response:

    # These strings are found in all successful connections:
    # If not found, exit with an error message
    if "<QRZDatabase " in xmlsessionfile:
        print("Connected to " + servername + "...")
        print("Captured XML is " + str(len(xmlsessionfile)) + " bytes long.")
        (startidx, endidx) = parsexml("GMTime>", xmlsessionfile)
        print("Session Timestamp:> " + xmlsessionfile[startidx:endidx] + " GMT")
        # msg = xmlsessionfile[startidx:endidx]
    else:
        error += 1  # Set error code bit 0
        print("\n*** ERROR: No response from {}.".format(servername))
        exit(error)  # Exit immediately.  This program cannot work without a communications link to the server.

    # These strings are found in unsuccessful logins:
    if "<Remark>" in xmlsessionfile:
        (startidx, endidx) = parsexml("Remark>", xmlsessionfile)
        msg = xmlsessionfile[startidx:endidx]
        print("QRZ Database Remark:> \"" + msg + "\"")

    if "<Error>" in xmlsessionfile:
        (startidx, endidx) = parsexml("Error>", xmlsessionfile)
        msg = xmlsessionfile[startidx:endidx]
        print("QRZ Database Error:> " + msg)
        error += 2  # Set error code bit 1
        print("\n*** ERROR: " + servername + " reported an error.")
        # exit("\n*** ERROR 2: QRZ database server reported an error.")

    # These strings are found in successful logins:
    if "<Count>" in xmlsessionfile:
        (startidx, endidx) = parsexml("Count>", xmlsessionfile)
        msg = xmlsessionfile[startidx:endidx]
        print("You have used this service " + msg + " times today.")

    if "<SubExp>" in xmlsessionfile:
        (startidx, endidx) = parsexml("SubExp>", xmlsessionfile)
        msg = xmlsessionfile[startidx:endidx]
        print("Subscription expires:> " + msg)

    if "<Key>" in xmlsessionfile:
        (startidx, endidx) = parsexml("Key>", xmlsessionfile)
        msg = xmlsessionfile[startidx:endidx]
        print("Your session key:> " + msg)
        key = msg
        # This is immediately after login. This is a brand new key - Save the key for later
        keyfile = open(keyfilename, 'w')
        keyfile.write(key)
        keyfile.close()
        print("*** Session key saved...\n")

    else: # No Session Key returned from server
        error += 2  # Set error bit 2
        print("\n*** ERROR: No Session Key returned from " + servername + ".")


else: # Session key file exists
    keyfile = open(keyfilename, "r")
    key = keyfile.read()
    keyfile.close()
    print("Session key retrieved from file...")

print("\n")
if error > 0:
    print("Error code: {}".format(error))
    exit(error) # Exit with error code if necessary

# if not "<Callsign>" in xmlsessionfile:
    # Retrieve search string from user:
#    searchcallSign = input("Enter call sign for search: ")

# Retrieve search string from file:

# BUG: with open statement - It is skipping every other line in searchcallSignfile & writing the email record twice
# possible remedy: changed .readline() to .read()
# This did not fix the bug.  It created an error because it is reading EOL characters as part of the data and using it
# as part of the full URL.  This causes an error, but it confirmed that it is starting on the second record.
# http.client.InvalidURL: URL can't contain control characters. '/xml/current/?s=74a1f32712cef52b448792ad50735989;callsign=W7RIM\nW5NEM\nKE5LUX\n...etc...
#                                                                                                                          ^^^^^-- Callsign in 2nd record
# Let's try default text mode, not 'r' - same result: starting with second record

searchcallSignfile = open(callsfilename, 'r', newline = '')
searchcallSignlist = searchcallSignfile.readlines()
searchcallSignfile.close()
# for eachline in searchcallSignlist:  # removing this line caused it to begin at the first record, but it won't loop!!!
for eachline in range (0,len(searchcallSignlist)):
    url = loginxmlurl + "current/?s=" + key + ";callsign=" + searchcallSignlist[eachline]
    xmlsessionfile = getxml(url)

    print("\n")
    # print(xmlsessionfile)  # Uncomment this statement for debugging purposes

# "Not all fields may be returned with each request. The field ordering is arbitrary and subject to change."
# qrz.com/XML/current_spec.html

# Parse XML response:

# These strings are found in all successful connections:
# If not found, exit with an error message
    if "<QRZDatabase " in xmlsessionfile:
            print("Connected to " + servername + "...")
            print("Captured XML is " + str(len(xmlsessionfile)) + " bytes long.")
            (startidx, endidx) = parsexml("GMTime>", xmlsessionfile)
            print("Session Timestamp:> " + xmlsessionfile[startidx:endidx] + " GMT")
            # msg = xmlsessionfile[startidx:endidx]
    else:
            error += 1
            searchcallSignfile.close()
            print("\n*** ERROR: No response from QRZ database server.")
            exit(1)

        # These strings are found in unsuccessful logins:
    if "<Remark>" in xmlsessionfile:
            (startidx, endidx) = parsexml("Remark>", xmlsessionfile)
            msg = xmlsessionfile[startidx:endidx]
            print("QRZ Database Remark:> \" {} \"").format(msg)

    if "<Error>" in xmlsessionfile:
            (startidx, endidx) = parsexml("Error>", xmlsessionfile)
            msg = xmlsessionfile[startidx:endidx]
            print("QRZ Database Error:> " + msg)
            error += 2
            searchcallSignfile.close()
            print("\n*** ERROR: " + servername + " reported an error.")
            exit(2)

        # These strings are found in successful logins:
    if "<Count>" in xmlsessionfile:
            (startidx, endidx) = parsexml("Count>", xmlsessionfile)
            msg = xmlsessionfile[startidx:endidx]
            print("You have used this service " + msg + " times today.")

    if "<SubExp>" in xmlsessionfile:
            (startidx, endidx) = parsexml("SubExp>", xmlsessionfile)
            msg = xmlsessionfile[startidx:endidx]
            print("Subscription expires:> " + msg)

    if "<Key>" in xmlsessionfile:
            (startidx, endidx) = parsexml("Key>", xmlsessionfile)
            msg = xmlsessionfile[startidx:endidx]
            print("Your session key:> " + msg)
            # This is immediately after a search query.  The keys may be the same - Saving the key may not be needed.
            if key != msg:
                keyfile = open(keyfilename, 'w')
                keyfile.write(msg) # save the new key
                keyfile.close()
                print("*** Session key saved...\n")
            key = msg # Regardless if new key == old key or new key != old key, make old key == new key

# else:  # No Session Key returned from server
#    print("\n*** ERROR 3: No Session Key returned from " + servername + ".")
#    error = 3

# if error > 0: exit(error) # Exit with error code if necessary

        # parse callsign fields
    if "<call>" in xmlsessionfile:
            (startidx, endidx) = parsexml("call>", xmlsessionfile)
            msg = xmlsessionfile[startidx:endidx]
            print("\nCallsign: " + msg)
            call = msg

        # parse xref field
    if "<xref>" in xmlsessionfile:
            (startidx, endidx) = parsexml("xref>", xmlsessionfile)
            msg = xmlsessionfile[startidx:endidx]
            print("Cross Reference: " + msg)
            xref = msg

        # parse aliases field
    if "<aliases>" in xmlsessionfile:
            (startidx, endidx) = parsexml("aliases>", xmlsessionfile)
            msg = xmlsessionfile[startidx:endidx]
            print("Aliases: " + msg)
            aliases = msg

        # parse dxcc field
    if "<dxcc>" in xmlsessionfile:
           (startidx, endidx) = parsexml("dxcc>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("DXCC Entity ID: " + msg)
           dxcc = msg

        # parse first name field
    if "<fname>" in xmlsessionfile:
            (startidx, endidx) = parsexml("fname>", xmlsessionfile)
            msg = xmlsessionfile[startidx:endidx]
            print("First Name: " + msg)
            fname = msg

        # parse last name field
    if "<name>" in xmlsessionfile:
            (startidx, endidx) = parsexml("name>", xmlsessionfile)
            msg = xmlsessionfile[startidx:endidx]
            print("Last Name: " + msg)
            name = msg

        # parse address line 1 field
    if "<addr1>" in xmlsessionfile:
            (startidx, endidx) = parsexml("addr1>", xmlsessionfile)
            msg = xmlsessionfile[startidx:endidx]
            print("Address Line 1: " + msg)
            addr1 = msg

        # parse address line 2 field
    if "<addr2>" in xmlsessionfile:
            (startidx, endidx) = parsexml("addr2>", xmlsessionfile)
            msg = xmlsessionfile[startidx:endidx]
            print("Address Line 2: " + msg)
            addr2 = msg

        # parse state field
    if "<state>" in xmlsessionfile:
            (startidx, endidx) = parsexml("state>", xmlsessionfile)
            msg = xmlsessionfile[startidx:endidx]
            print("State: " + msg)
            state = msg

        # parse zip field
    if "<zip>" in xmlsessionfile:
            (startidx, endidx) = parsexml("zip>", xmlsessionfile)
            msg = xmlsessionfile[startidx:endidx]
            print("ZIP Code: " + msg)
            zip = msg

        # parse country field
    if "<country>" in xmlsessionfile:
           (startidx, endidx) = parsexml("country>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("Country: " + msg)
           country = msg

        # parse dxcc entity code field
    if "<ccode>" in xmlsessionfile:
           (startidx, endidx) = parsexml("ccode>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("DXCC Entity Code: " + msg)
           ccode = msg

        # parse latitude field
    if "<lat>" in xmlsessionfile:
           (startidx, endidx) = parsexml("lat>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("Latitude: " +msg)
           lat = msg

        # parse longitude field
    if "<lon>" in xmlsessionfile:
           (startidx, endidx) = parsexml("lon>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("Longitude: " +msg)
           lon = msg

        # parse grid locator field
    if "<grid>" in xmlsessionfile:
           (startidx, endidx) = parsexml("grid>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("Grid Locator: " +msg)
           grid = msg

        # parse county field
    if "<county>" in xmlsessionfile:
            (startidx, endidx) = parsexml("county>", xmlsessionfile)
            msg = xmlsessionfile[startidx:endidx]
            print("County: " +msg)
            county = msg

        # parse FIPS county identifier field
    if "<fips>" in xmlsessionfile:
           (startidx, endidx) = parsexml("fips>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("FIPS: " +msg)
           fips = msg

        # parse land field
    if "<land>" in xmlsessionfile:
           (startidx, endidx) = parsexml("land>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("DXCC Country: " +msg)
           land = msg

        # parse license effective date field
    if "<efdate>" in xmlsessionfile:
            (startidx, endidx) = parsexml("efdate>", xmlsessionfile)
            msg = xmlsessionfile[startidx:endidx]
            # Clean up this field with datetime if necessary
            print("License Effective Date: " +msg)
            efdate = msg

        # parse license expiration date field
    if "<expdate>" in xmlsessionfile:
            (startidx, endidx) = parsexml("expdate>", xmlsessionfile)
            msg = xmlsessionfile[startidx:endidx]
            # Clean up this field with datetime if necessary
            print("License Expiration Date: " +msg)
            expdate = msg

        # parse previous callsign field
    if "<p_call>" in xmlsessionfile:
            (startidx, endidx) = parsexml("p_call>", xmlsessionfile)
            msg = xmlsessionfile[startidx:endidx]
            print("Previous Callsign: " +msg)
            p_call = msg

        # parse license class field
    if "<class>" in xmlsessionfile:
            (startidx, endidx) = parsexml("class>", xmlsessionfile)
            msg = xmlsessionfile[startidx:endidx]
            print("License Class: " +msg)
            license_class = msg

        # parse license type codes field
    if "<codes>" in xmlsessionfile:
           (startidx, endidx) = parsexml("codes>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("License Type Codes: " +msg)
           license_codes = msg

        # parse QSL Manager field
    if "<qslmgr>" in xmlsessionfile:
           (startidx, endidx) = parsexml("qslmgr>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("QSL Manager: " +msg)
           qslmgr = msg

        # moved email address to end as a condition to write the record to a csv file
        # parse email address field
        # if "<email>" in xmlsessionfile:
        #     (startidx, endidx) = parsexml("email>", xmlsessionfile)
        #     msg = xmlsessionfile[startidx:endidx]
        #     print("Email Address: " +msg)
        #     email = msg

        # parse QRZ webpage URL field
    if "<url>" in xmlsessionfile:
           (startidx, endidx) = parsexml("url>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("QRZ webpage URL: " +msg)
           qrz_webpage_addr = msg

        # parse QRZ webpage views field
    if "<u_views>" in xmlsessionfile:
           (startidx, endidx) = parsexml("u_views>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("QRZ webpage views: " +msg)
           u_views = msg

        # parse biography length field
    if "<bio>" in xmlsessionfile:
           (startidx, endidx) = parsexml("bio>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("QRZ Biography length (bytes): " +msg)
           bio = msg

        # parse biography update date field
    if "<biodate>" in xmlsessionfile:
           (startidx, endidx) = parsexml("biodate>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           # Clean up this field with datetime if necessary
           print("QRZ Biography last update: " +msg)
           biodate = msg

        # parse image field
    if "<image>" in xmlsessionfile:
           (startidx, endidx) = parsexml("image>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("Image URL: " +msg)
           image = msg

        # parse image specifications field
    if "<imageinfo>" in xmlsessionfile:
           (startidx, endidx) = parsexml("imageinfo>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("Image specifications (height:width:bytes): " +msg)
           imageinfo = msg

        # parse QRZ database serial number field
    if "<serial>" in xmlsessionfile:
           (startidx, endidx) = parsexml("serial>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("QRZ Database Serial #: " +msg)
           serial = msg

        # parse QRZ callsign last modified date field
    if "<moddate>" in xmlsessionfile:
           (startidx, endidx) = parsexml("moddate>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           # Clean up this field with datetime if necessary
           print("QRZ callsign last modified date: " +msg)
           moddate = msg

        # parse USPS Metro Service Area field
    if "<MSA>" in xmlsessionfile:
           (startidx, endidx) = parsexml("MSA>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("USPS Metro Service Area: " +msg)
           MSA = msg

        # parse Telephone Area Code field
    if "<AreaCode>" in xmlsessionfile:
           (startidx, endidx) = parsexml("AreaCode>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("Telephone Area Code: " +msg)
           AreaCode = msg

        # parse Time Zone field
    if "<TimeZone>" in xmlsessionfile:
           (startidx, endidx) = parsexml("TimeZone>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("Time Zone: " +msg)
           TimeZone = msg

        # parse GMT Offset field
    if "<GMTOffset>" in xmlsessionfile:
           (startidx, endidx) = parsexml("GMTOffset>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("GMT Offset: " +msg)
           GMTOffset = msg

        # parse Daylight Savings Time Observed field
    if "<DST>" in xmlsessionfile:
           (startidx, endidx) = parsexml("DST>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("Observes Daylight Savings Time: " +msg)
           DST = msg

        # parse eQSL field
    if "<eqsl>" in xmlsessionfile:
           (startidx, endidx) = parsexml("eqsl>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("Accepts eQSL: " +msg)
           eqsl = msg

        # parse paper QSL field
    if "<mqsl>" in xmlsessionfile:
           (startidx, endidx) = parsexml("mqsl>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("Returns paper QSL: " +msg)
           mqsl = msg

        # parse CQ Zone Identifier field
    if "<cqzone>" in xmlsessionfile:
           (startidx, endidx) = parsexml("cqzone>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("CQ Zone Identifier: " +msg)
           cqzone = msg

        # parse ITU Zone Identifier field
    if "<ituzone>" in xmlsessionfile:
           (startidx, endidx) = parsexml("ituzone>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("ITU Zone Identifier: " +msg)
           ituzone = msg

        # parse year of birth field
    if "<born>" in xmlsessionfile:
           (startidx, endidx) = parsexml("born>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("Year of Birth: " +msg)
           born = msg

        # parse QRZ record manager field
    if "<user>" in xmlsessionfile:
           (startidx, endidx) = parsexml("user>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("QRZ Database Record Manager: " +msg)
           user = msg

        # parse Accepts Logbook of the World QSL field
    if "<lotw>" in xmlsessionfile:
           (startidx, endidx) = parsexml("lotw>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("Accepts LOTW: " +msg)
           lotw = msg

        # parse IOTA Designator field
    if "<iota>" in xmlsessionfile:
           (startidx, endidx) = parsexml("iota>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("IOTA Designator: " +msg)
           iota = msg

        # parse Source of latitude/longitude data field
    if "<geoloc>" in xmlsessionfile:
           (startidx, endidx) = parsexml("geoloc>", xmlsessionfile)
           msg = xmlsessionfile[startidx:endidx]
           print("Source of Lat/Long: " +msg)
           geoloc = msg

        # parse email address field
    if "<email>" in xmlsessionfile:
            (startidx, endidx) = parsexml("email>", xmlsessionfile)
            msg = xmlsessionfile[startidx:endidx]
            print("Email Address: " +msg)
            email = msg

            # Open csv formatted file - 'a'ppend csv records
            csvFile = open(csvfilename, 'a', newline='')
            writer = csv.writer(csvFile)

            writer.writerow([call, xref, aliases, dxcc, fname, name, addr1, addr2, state, zip, country, ccode, lat,
                             lon, grid, county, fips, land, efdate, expdate, p_call, license_class, license_codes,
                             qslmgr, email, qrz_webpage_addr, u_views, bio, biodate, image, imageinfo, serial, moddate,
                             MSA, AreaCode, TimeZone, GMTOffset, DST, eqsl, mqsl, cqzone, ituzone, born, user, lotw,
                             iota, geoloc])
            csvFile.close()
            print("\n*** Callsign saved to csv file...\n")
searchcallSignfile.close()
print("Processed " + str(eachline + 1) + " records")
exit()
