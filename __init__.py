'''
Created on OCT 27, 2018

@author: HaiViet
'''

# import libraries
import urllib 
from bs4 import BeautifulSoup
from urllib.request import urlopen
import pandas as pd
from datetime import datetime
import xmltodict
import os
from collections import OrderedDict
import sys
import traceback
import re
import configparser 

def listRecursive (d, key):
    for k, v in d.items ():
        if isinstance (v, OrderedDict):
            for found in listRecursive (v, key):
                yield found
        if k == key:
            yield v
            
def replacenth(string, sub, wanted, n):
    where = [m.start() for m in re.finditer(sub, string)][n-1]
    before = string[:where]
    after = string[where:]
    after = after.replace(sub, wanted, 1)
    newString = before + after
    return newString

configParser = configparser.RawConfigParser()   
configFilePath = r'init.conf'
configParser.read(configFilePath)

inputFilePath=configParser.get('Init-config', 'inputFilePath')
sheetName=configParser.get('Init-config', 'sheetName')
xmlpath=configParser.get('Init-config', 'xmlpath')
outputFilePath=configParser.get('Init-config', 'outputFilePath')
errorFilePath=configParser.get('Init-config', 'errorFilePath')

#Create folder for contains xml file
if not os.path.exists(xmlpath):
    os.makedirs(xmlpath)
#Read file input
xl_file = pd.ExcelFile(inputFilePath)
df = xl_file.parse(sheetName)
csvFile=open(outputFilePath,"w+")
csvFile.write("ticker,cik,cname,formtype,secdate,owner,Column2_trandate,seqnum,Column3_code,Column4_ (A) or (D),Column6,Column4_shareamount,Footnote#,Footnote_explanation,URL,XML,text\n")
errorLogFile=open(errorFilePath,"w+")
errorLogFile.write("ticker,cik,cname,formtype,secdate,owner,Column2_trandate,seqnum,Column3_code,Column4_ (A) or (D),Column6,Column4_shareamount,description")
for i in df.index:
    dateCheck=df['secdate'][i].strftime('%Y-%m-%d')
    owner=df['owner'][i]
    ownerFname=owner.split(" ")[0]
    ''.join(e for e in ownerFname if e.isalnum())
    ownerFname=ownerFname.upper(); 
    transdate=df['Column2_trandate'][i].strftime('%Y-%m-%d')
    col4=df['Column4_ (A) or (D)'][i]
    col4Share="{:10.4f}".format(df['Column4_shareamount'][i]).strip()
    col4Share=float(col4Share)
    print(col4Share)
    cik='000'+str(df['cik'][i]).split('.0')[0]
    ticker=df['ticker'][i]
    cname="\""+df['cname'][i]+"\""
    formtype=df['formtype'][i]
    secdate=df['secdate'][i]
    seqnum=str(df['seqnum'][i])
    Column6=df['column6'][i]
    if(df['cik'][i]==""): 
        cik=ticker
    if(cik=="000nan"):
        cik=ticker
    #Params for get
    params= {'action':'getcompany','CIK':cik, 'type':df['formtype'][i],'dateb':df['secdate'][i].strftime('%Y%m%d'),'owner':'include','count':'100'}
    print('https://www.sec.gov/cgi-bin/browse-edgar?'+urllib.parse.urlencode(params))
    resp = urlopen('https://www.sec.gov/cgi-bin/browse-edgar?'+urllib.parse.urlencode(params))
    linkMain='https://www.sec.gov/cgi-bin/browse-edgar?'+urllib.parse.urlencode(params)
    #print('https://www.sec.gov/cgi-bin/browse-edgar?'+urllib.parse.urlencode(params))
    soup = BeautifulSoup(resp.read(),'html.parser')
    table = soup.find("table", attrs={'class': 'tableFile2'})
    
    try:
        table.findAll('tr');
    except Exception as e:
        params= {'action':'getcompany','company':cname, 'match':'contain', 'type':df['formtype'][i],'dateb':df['secdate'][i].strftime('%Y%m%d'),'owner':'include','count':'100'}
        resp = urlopen('https://www.sec.gov/cgi-bin/browse-edgar?'+urllib.parse.urlencode(params))
        linkMain='https://www.sec.gov/cgi-bin/browse-edgar?'+urllib.parse.urlencode(params)
        #print('https://www.sec.gov/cgi-bin/browse-edgar?'+urllib.parse.urlencode(params))
        soup = BeautifulSoup(resp.read(),'html.parser')
        table = soup.find("table", attrs={'class': 'tableFile2'})
    isHaving = False;
    datasets = []
    xmlDocCount=1;
    try:
        isWrite=False;
        for row in table.findAll('tr'):
            i=0
            link="https://www.sec.gov/"
            for td in row.find_all("td"):
                if(i==1):
                    link+=td.a.get("href")
                if(i==3): #Check if date is equal
                    if(td.text==str(dateCheck)):
                        #print(link)   
                        respDocs  = urlopen(link)
                        soupDocs  = BeautifulSoup(respDocs.read(),'html.parser')
                        tableDocs = soupDocs.find("table", attrs={'class': 'tableFile'})
                        #Access to link Docs
                        x=0
                        linkDocs="https://www.sec.gov/"
                        htmlLinkDat="https://www.sec.gov/"
                        textLinkDat="https://www.sec.gov/"
                        col3_code="G"
                        resultrow="";
                        for rowDocs in tableDocs.findAll('tr'):
                            z=0
                            x+=1
                            for tdDocs in rowDocs.find_all("td"):
                                if(z==2 and x==2):
                                    htmlLinkDat=htmlLinkDat+tdDocs.a.get("href")
                                if(z==2 and x==4):
                                    textLinkDat=textLinkDat+tdDocs.a.get("href")   
                                    resultrow.replace("textLink", textLinkDat)
                                    if(isWrite): csvFile.write(resultrow)
                                    else: resultrow = ""
                                    isHaving = isWrite
                                if(z==2 and x==3):
                                    linkDocs=linkDocs+tdDocs.a.get("href")
                                    print(linkDocs)
                                    xmlFile = urlopen(linkDocs).read()
                                    xmlDoc = xmltodict.parse(xmlFile)
                                    try:
                                        xmlDoc["ownershipDocument"]["nonDerivativeTable"]["nonDerivativeTransaction"]
                                    except Exception as e:
                                        if(xmlFile.count(b"<nonDerivativeSecurity>")<1):
                                            xmlFile =xmlFile.replace(b"<nonDerivativeSecurity>",b"<nonDerivativeTable><nonDerivativeTransaction>")
                                            xmlFile =xmlFile.replace(b"</nonDerivativeSecurity>",b"</nonDerivativeTransaction></nonDerivativeTable>")
                                            xmlDoc = xmltodict.parse(xmlFile)
                                        else:
                                            xmlFile =xmlFile.replace(b"<nonDerivativeSecurity>",b"<nonDerivativeTable><nonDerivativeSecurity>",1)
                                            xmlFile =replacenth(xmlFile,
                                                                b"</nonDerivativeSecurity>",
                                                                b"</nonDerivativeSecurity></nonDerivativeTable>",
                                                                xmlFile.count(b"</nonDerivativeSecurity>"))
                                            xmlFile =xmlFile.replace(b"nonDerivativeSecurity",b"nonDerivativeTransaction")
                                            xmlDoc = xmltodict.parse(xmlFile)
                                    try:
                                        xmlDoc["ownershipDocument"]["nonDerivativeTable"]["nonDerivativeTransaction"]
                                    except Exception as e:
                                        xmlFile =xmlFile.replace(b"<derivativeTable>",b"<nonDerivativeTable>")
                                        xmlFile =xmlFile.replace(b"</derivativeTable>",b"</nonDerivativeTable>")
                                        xmlFile =xmlFile.replace(b"<derivativeTransaction>",b"<nonDerivativeTransaction>")
                                        xmlFile =xmlFile.replace(b"</derivativeTransaction>",b"</nonDerivativeTransaction>")
                                        xmlFile=xmlFile.replace(b"nonDerivativeHolding",b"nonDerivativeTransaction")
                                        xmlDoc = xmltodict.parse(xmlFile)
                                    xmlFile=xmlFile.replace(b"nonDerivativeHolding",b"nonDerivativeTransaction")
                                    xmlDoc = xmltodict.parse(xmlFile)
                                    checkOwner =False;
                                    try:
                                        if(ownerFname in xmlDoc["ownershipDocument"]["reportingOwner"]["reportingOwnerId"]["rptOwnerName"].upper()): checkOwner=True;
                                    except Exception as e:
                                        for found in xmlDoc["ownershipDocument"]["reportingOwner"]:
                                            print("aaaa")
                                            print(found["reportingOwnerId"]["rptOwnerName"])
                                            if(ownerFname in found["reportingOwnerId"]["rptOwnerName"].upper()): 
                                                checkOwner=True
                                    
                                    
                                    f = open(xmlpath+"\\"+str(cik)+"_"+str(transdate)+"_"+str(xmlDocCount)+".xml","w+")
                                    f.write(xmltodict.unparse(xmlDoc))
                                    f.close()
                                    xmlDocCount=xmlDocCount+1;
                                    if(checkOwner):
                                        try:
                                            footnoteNo=""
                                            footNotedef=""
                                            for data in xmlDoc["ownershipDocument"]["nonDerivativeTable"]["nonDerivativeTransaction"]:
                                                if(isinstance(data, dict)): 
                                                    print(data["transactionAmounts"]["transactionShares"]["value"]);
                                                    if(  (transdate == data["transactionDate"]["value"])
                                                       & (data["transactionAmounts"]["transactionAcquiredDisposedCode"]["value"] == col4)
                                                       & (col4Share == float(data["transactionAmounts"]["transactionShares"]["value"]))
                                                       & (data["transactionCoding"]["transactionCode"] in ("G"))
                                                       & (Column6 == data["ownershipNature"]["directOrIndirectOwnership"]["value"])):
                                                        print(data["securityTitle"]["value"])                                                   
                                                        isfn=True
                                                        for found in listRecursive(data,"footnoteId"): 
                                                            isfn=False
                                                            isTake=0
                                                            try:
                                                                footNoteList =  found.items()
                                                            except Exception as e:
                                                                footNoteList = found[0].items()
                                                            for key, value in footNoteList:
                                                                if(footnoteNo == value): break;
                                                                footnoteNo = value
                                                                for footList in xmlDoc["ownershipDocument"]["footnotes"]["footnote"]:
                                                                    if(isinstance(footList,str)): 
                                                                            footNotedef = xmlDoc["ownershipDocument"]["footnotes"]["footnote"]["#text"]
                                                                            footNotedef = footNotedef.replace("\"", "'")
                                                                            footNotedef ="\""+footNotedef+"\""
                                                                            footNotedef = footNotedef.replace("\n"," ")
                                                                            footNotedef = footNotedef.replace("\r","")
                                                                            resultrow=resultrow+ ticker+","+str(cik)+","+cname+","+str(formtype)+","+dateCheck+","+owner+","+transdate+","+str(seqnum)+","+col3_code+","+col4+","+Column6+","+str(col4Share)+","+footnoteNo+","+footNotedef+","+htmlLinkDat+","+linkDocs+","+"textLink\n";
                                                                            isTake=1
                                                                            break;
                                                                    else:    
                                                                        for key1, value1 in footList.items():
                                                                            if(key1=="@id" and value1==footnoteNo):
                                                                                isTake=1
                                                                            if(key1=="#text" and isTake==1):
                                                                                footNotedef = value1
                                                                                footNotedef = footNotedef.replace("\"", "'")
                                                                                footNotedef ="\""+footNotedef+"\""
                                                                                footNotedef = footNotedef.replace("\n"," ")
                                                                                footNotedef = footNotedef.replace("\r","")
                                                                                resultrow=resultrow+ ticker+","+str(cik)+","+cname+","+str(formtype)+","+dateCheck+","+owner+","+transdate+","+str(seqnum)+","+col3_code+","+col4+","+Column6+","+str(col4Share)+","+footnoteNo+","+footNotedef+","+htmlLinkDat+","+linkDocs+","+"textLink\n";
                                                                                isTake=1
                                                                                break;
                                                                            #if(isTake==1):  break;
                                                                    if(isTake==1): break;
                                                                if(isTake==1): break;
                                                            #if(isTake==1): break;    
                                                        if(isfn): 
                                                            resultrow=resultrow+ ticker+","+str(cik)+","+cname+","+str(formtype)+","+dateCheck+","+owner+","+transdate+","+str(seqnum)+","+col3_code+","+col4+","+Column6+","+str(col4Share)+","+footnoteNo+","+footNotedef+","+htmlLinkDat+","+linkDocs+","+"textLink\n";
                                                        isWrite =True
                                                           
                                                else:
                                                    if(  (transdate == xmlDoc["ownershipDocument"]["nonDerivativeTable"]["nonDerivativeTransaction"]["transactionDate"]["value"])
                                                       & (xmlDoc["ownershipDocument"]["nonDerivativeTable"]["nonDerivativeTransaction"]["transactionAmounts"]["transactionAcquiredDisposedCode"]["value"] == col4)
                                                       & (col4Share == float(xmlDoc["ownershipDocument"]["nonDerivativeTable"]["nonDerivativeTransaction"]["transactionAmounts"]["transactionShares"]["value"]))
                                                       & (xmlDoc["ownershipDocument"]["nonDerivativeTable"]["nonDerivativeTransaction"]["transactionCoding"]["transactionCode"] in ("G"))
                                                       & (Column6 == xmlDoc["ownershipDocument"]["nonDerivativeTable"]["nonDerivativeTransaction"]["ownershipNature"]["directOrIndirectOwnership"]["value"])):
                                                        for data2 in [xmlDoc["ownershipDocument"]["nonDerivativeTable"]["nonDerivativeTransaction"]]:
                                                            print(data2["securityTitle"]["value"])
                                                            isfn=True
                                                            for found in listRecursive(data2,"footnoteId"): 
                                                                isfn=False
                                                                isTake=0
                                                                try:
                                                                    footNoteList =  found.items()
                                                                except Exception as e:
                                                                    footNoteList = found[0].items()
                                                                for key, value in footNoteList:
                                                                    if(footnoteNo==value): print(footnoteNo+value); break;
                                                                    print(footnoteNo+value+"ok")
                                                                    footnoteNo = value
                                                                    for footList in xmlDoc["ownershipDocument"]["footnotes"]["footnote"]:
                                                                        if(isinstance(footList,str)): 
                                                                            footNotedef = xmlDoc["ownershipDocument"]["footnotes"]["footnote"]["#text"]
                                                                            footNotedef = footNotedef.replace("\"", "'")
                                                                            footNotedef ="\""+footNotedef+"\""
                                                                            footNotedef = footNotedef.replace("\n"," ")
                                                                            footNotedef = footNotedef.replace("\r","")
                                                                            resultrow=resultrow+ str(ticker)+","+str(cik)+","+cname+","+str(formtype)+","+dateCheck+","+owner+","+transdate+","+str(seqnum)+","+col3_code+","+col4+","+Column6+","+str(col4Share)+","+footnoteNo+","+footNotedef+","+htmlLinkDat+","+linkDocs+","+"textLink\n";
                                                                            isTake=1
                                                                            break;
                                                                        else:    
                                                                            for key1, value1 in footList.items():
                                                                                if(key1=="@id" and value1==footnoteNo):
                                                                                    isTake=1
                                                                                if(key1=="#text" and isTake==1):
                                                                                    footNotedef = value1
                                                                                    footNotedef = footNotedef.replace("\"", "'")
                                                                                    footNotedef ="\""+footNotedef+"\""
                                                                                    footNotedef = footNotedef.replace("\n"," ")
                                                                                    footNotedef = footNotedef.replace("\r","")
                                                                                    resultrow=resultrow+ ticker+","+str(cik)+","+cname+","+str(formtype)+","+dateCheck+","+owner+","+transdate+","+str(seqnum)+","+col3_code+","+col4+","+Column6+","+str(col4Share)+","+footnoteNo+","+footNotedef+","+htmlLinkDat+","+linkDocs+","+"textLink\n";
                                                                                    isTake=1
                                                                                    break;
                                                                                #if(isTake==1):  break;
                                                                        if(isTake==1): break;
                                                                    if(isTake==1): break;
                                                                #if(isTake==1): break;    
                                                            if(isfn): 
                                                                resultrow=resultrow+ ticker+","+str(cik)+","+cname+","+str(formtype)+","+dateCheck+","+owner+","+transdate+","+str(seqnum)+","+col3_code+","+col4+","+Column6+","+str(col4Share)+","+footnoteNo+","+footNotedef+","+htmlLinkDat+","+linkDocs+","+"textLink\n";
                                                            isWrite =True
                                                    break;
                                        except Exception as e:
                                            print(e)
                                            try:
                                                errorRow=ticker+","+str(cik)+","+cname+","+str(formtype)+","+dateCheck+","+owner+","+transdate+","+str(seqnum)+","+col3_code+","+col4+","+Column6+","+str(col4Share)+","+str(e);
                                                errorLogFile.write("\n"+errorRow)
                                            except Exception as e:
                                                print("")   
                                            
                                    
                                z+=1
                            
                i+=1
        if(isHaving==False):
            errorRow=ticker+","+str(cik)+","+cname+","+str(formtype)+","+dateCheck+","+owner+","+transdate+","+str(seqnum)+","+col3_code+","+col4+","+Column6+","+str(col4Share)+", No match filter";
            errorLogFile.write("\n"+errorRow)
    except Exception as e:
        print(xmlDoc)
        print(cik)
        print(e)
        print(linkMain)
        traceback.print_exc()
        try:
            errorRow=ticker+","+str(cik)+","+cname+","+str(formtype)+","+dateCheck+","+owner+","+transdate+","+str(seqnum)+","+col3_code+","+col4+","+Column6+","+str(col4Share)+","+str(e);
            errorLogFile.write("\n"+errorRow)
        except Exception as e:
            print("")
csvFile.close()
errorLogFile.close()



