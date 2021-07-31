import requests
import bs4
import re
from xml.dom import minidom
#
# Specify a callsign
searchValue = input("Enter search value: ")
#
# Retrieve XML record from FCC API
rooturl = 'http://data.fcc.gov/api/license-view/basicSearch/getLicenses?searchValue='
url = rooturl + searchValue
print("Retrieving general XML record from FCC database...")
try:
    fccResp = requests.get(url, timeout = 5)
except:
    if fccResp.status_code != 200:
        print(f"FCC API Error: {fccResp}")
        exit()
#
# Parse XML record for details
print("Parsing XML record...")
fccRecord = minidom.parseString(fccResp.text)
try:
    fccRecordTree = fccRecord.getElementsByTagName('License')[0]
except IndexError:
    errorTree = fccRecord.getElementsByTagName('Errors')[0]
    errorElement = errorTree.childNodes.item(0)
    errorCode = errorElement.getAttribute('code')
    errorMsg = errorElement.getAttribute('msg')
    print(f"\nSearch Error Code: {errorCode}")
    print(f"{errorMsg}\n")
    exit()
fccLicenseTree = fccRecordTree.childNodes
try:
    name = fccLicenseTree[0].childNodes.item(0).nodeValue
except AttributeError:
    name = ''
try:
    frn = fccLicenseTree[1].childNodes.item(0).nodeValue
except AttributeError:
    frn = ''
try:
    callSign = fccLicenseTree[2].childNodes.item(0).nodeValue
except AttributeError:
    callSign = ''
try:
    categoryDesc = fccLicenseTree[3].childNodes.item(0).nodeValue
except AttributeError:
    categoryDesc = ''
try:
    serviceDesc = fccLicenseTree[4].childNodes.item(0).nodeValue
except AttributeError:
    serviceDesc = ''
try:
    statusDesc = fccLicenseTree[5].childNodes.item(0).nodeValue
except AttributeError:
    statusDesc = ''
try:
    expDate = fccLicenseTree[6].childNodes.item(0).nodeValue
except AttributeError:
    expDate = ''
try:
    licenseID = fccLicenseTree[7].childNodes.item(0).nodeValue
except AttributeError:
    licenseID = ''
try:
    webpage = fccLicenseTree[8].childNodes.item(0).nodeValue
except AttributeError:
    webpage = ''
#
# Retrieve address and license class from detailed FCC record from url in XML
if webpage == '':
    print("Detailed webpage not available...")
    exit()
#
print("Retrieving detailed HTML page from FCC database...")
try:
    detailsResp = requests.get(webpage, timeout = 5)
except:
    if detailsResp.status_code != 200:
        print(f"ULS Database Error: {detailsResp}")
        exit()
#
print("Parsing HTML document...")
soup = bs4.BeautifulSoup(detailsResp.text, 'html5lib')
licNameAddrStyle = 'body > table:nth-child(4) > tbody > tr > td:nth-child(2) > div > table:nth-child(2) > tbody > tr:nth-child(4) > td > table > tbody > tr:nth-child(3) > td:nth-child(1)'
licTypeStyle = 'body > table:nth-child(4) > tbody > tr > td:nth-child(2) > div > table:nth-child(2) > tbody > tr:nth-child(4) > td > table > tbody > tr:nth-child(1) > td:nth-child(4)'
licClassStyle = 'body > table:nth-child(4) > tbody > tr > td:nth-child(2) > div > table:nth-child(2) > tbody > tr:nth-child(6) > td > table > tbody > tr:nth-child(1) > td:nth-child(2)'
licFonEmailStyle = 'body > table:nth-child(4) > tbody > tr > td:nth-child(2) > div > table:nth-child(2) > tbody > tr:nth-child(4) > td > table > tbody > tr:nth-child(3) > td:nth-child(2) > p'
#
licNameAddr = soup.select(licNameAddrStyle)[0].text.lstrip().split('\n')
licAddr = licNameAddr[1]
licAddr2 = licNameAddr[2].split(', ')
if len(licAddr2) == 2:
    licCity = licAddr2[0]
    licState = licAddr2[1]
else:
    licCity = ''
    licState = ''
licZip = licNameAddr[3]
if len(licNameAddr) == 6:
    licAttn = licNameAddr[5]
else:
    licAttn = ''
#
licType = soup.select(licTypeStyle)[0].text.strip()
#
licClass = soup.select(licClassStyle)[0].text.strip()
#
fonRegEx = '\(\d{3}\)\d{3}-\d{4}'
licFonEmail = soup.select(licFonEmailStyle)[0].text.strip().split(':')
if len(licFonEmail) > 1:
    fonObj = re.search(fonRegEx,licFonEmail[1].strip())
    licFon = fonObj.group()
else:
    licFon = ''
if len(licFonEmail) > 2:
    fonObj = re.search(fonRegEx,licFonEmail[2].strip())
    licFax = fonObj.group()
else:
    licFax = ''
if len(licFonEmail) == 4:
    licEmail = licFonEmail[3]
else:
    licEmail = ''
#
#print(name,frn,callSign,categoryDesc,serviceDesc,statusDesc,expDate,licenseID,webpage)
#print(licAddr,licCity,licState,licZip,licAttn,licClass,licFon,licFax,licEmail)
#
print(f"\nName           : {name}")
print(f"Address        : {licAddr}")
print(f"City, State ZIP: {licCity}, {licState} {licZip}")
print(f"                 {licAttn}")
print(f"Phone          : {licFon}")
print(f"Fax            : {licFax}")
print(f"Email          : {licEmail}\n")
print(f"FRN            : {frn}")
print(f"Callsign       : {callSign}")
print(f"Type           : {licType}")
print(f"Class          : {licClass}")
print(f"Category       : {categoryDesc}")
print(f"Service        : {serviceDesc}")
print(f"Expiration Date: {expDate}")
#
