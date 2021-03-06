# Copyright (c) 2018 by Stefan Lieberth <stefan@lieberth.net>.
# All rights reserved.
#
# This program and the accompanying materials are made available under
# the terms of the Eclipse Public License v1.0 which accompanies this
# distribution and is available at:
#
#     http://www.eclipse.org/legal/epl-v10.html
#
# Contributors:
#     Stefan Lieberth - initial implementation, API, and documentation

#  \version   0.1.1
#  \date      01.02.2018
#  \modification:
#  0.1.1 - get started


import asyncio
import random
import logging
import yaml
from copy import deepcopy
import pprint
import re
import datetime
from jinja2 import Template, Environment

def _isInDictionary (searchKey,inDictionary,defaultValue):
    if searchKey in inDictionary.keys():
        return inDictionary[searchKey]
    else:
        return defaultValue 

def _substitudeValueOld (myObject,valueList):
    logging.info ('substitudeValue: {} valuelist {}'.format(myObject,valueList))
    if type(myObject) == str:
        reCurlyBracketPattern = re.compile(r'\{\{\d+\}\}')
        substitudeList = reCurlyBracketPattern.findall(myObject)
        if len(substitudeList) > 0:
            if len(substitudeList) == 1:
                substitudeValue = valueList[int(substitudeList[0][2:-2])]
                if myObject == substitudeList[0]:
                    return substitudeValue
                else:
                    return myObject.replace(substitudeList[0],str(substitudeValue))
            else:
                returnString = myObject
                for substitudeCurlyBracketParameterString in substitudeList:
                    #print (int(substitudeCurlyBracketParameterString[2:-2]))
                    substitudeValue = valueList[int(substitudeCurlyBracketParameterString[2:-2])]
                    returnString = returnString.replace(substitudeCurlyBracketParameterString,str(substitudeValue))
                    #print (returnString)
                return returnString        
        else:
            return myObject
    else:                    
        return myObject  

def _substitudeValue (myObject,valueMatrix=[[]],varDict={},loopIndex=0,stepIndex=0):
    logging.debug ('substitudeValue: {} valueMatrix {} varDict {}'.format(myObject,valueMatrix,varDict))
#     if varDict == {}:
#         if type(myObject) == str:
#             reCurlyBracketPattern = re.compile(r'\{\{\d+\}\}')
#             substitudeList = reCurlyBracketPattern.findall(myObject)
#             if len(substitudeList) > 0:
#                 if len(substitudeList) == 1:
#                     try:
#                         substitudeValue = valueMatrix[loopIndex][int(substitudeList[0][2:-2])]
#                     except:
#                         substitudeValue = "substitudeValueERROR"
#                     if myObject == substitudeList[0]:
#                         return substitudeValue
#                     else:
#                         return myObject.replace(substitudeList[0],str(substitudeValue))
#                 else:
#                     returnString = myObject
#                     for substitudeCurlyBracketParameterString in substitudeList:
#                         try:
#                             substitudeValue = valueMatrix[loopIndex][int(substitudeCurlyBracketParameterString[2:-2])]
#                         except:
#                             substitudeValue = "substitudeValueERROR"
#                         returnString = returnString.replace(substitudeCurlyBracketParameterString,str(substitudeValue))
#                         #print (returnString)
#                     return returnString        
#             else:
#                 return myObject
#         else:                    
#             return myObject
#     else:
    if isinstance(myObject,str):
        try:
            template = Template(myObject) 
            renderedString = template.render(varDict,loopIndex=loopIndex,stepIndex=stepIndex) 
        except:
            logging.error("_substitudeValue jinja2 rendering error")
            return myObject
        else:
            return renderedString
    else:
        logging.error("_substitudeValue jinja2 not yet implemented just for strings")
        return myObject


def _substitudeMacro (myObject,macroDict={}):
    macro_jinja_env = Environment(\
        block_start_string = '\MACRO_BLOCK{{',
        block_end_string = '}}',
        variable_start_string = '\MACRO_VAR{{',
        variable_end_string = '}}',
        comment_start_string = '\#{',
        comment_end_string = '}',
        line_statement_prefix = '%-',
        line_comment_prefix = '%#',
        trim_blocks = True,
        autoescape = False,
        loader = jinja2.FileSystemLoader("."))
    logging.debug (' _substitudeMacro: {} macroDict {} '.format(myObject,macroDict))


def _addTimeStampsToStepDict(t1,stepDict,commandCounter=0):
    t2=datetime.datetime.now()
    stepDict["output"][commandCounter]["endTS"] = t2.strftime('%Y-%m-%d %H:%M:%S.%f')   
    stepDict["output"][commandCounter]["elapsed"] = str((t2-t1))
    stepDict["output"][commandCounter]["elapsedRaw"] = (t2-t1).total_seconds()

def _createOutputList(step,stepType,stepDict,loopCounter):
    stepDict["output"] = []
    def enrichOutputContainer(i,command):
        outputContainer = {}
        if "device" in stepDict.keys():
            outputContainer["device"] = stepDict["device"]
        outputContainer["loopCounter"] = loopCounter
        outputContainer["stepCounter"] = step
        outputContainer["commandCounter"] = i + 1
        outputContainer["stepType"] = stepType
        outputContainer["commandOrig"] = str(command).replace("+","")
        outputContainer["pass"] = True  #default
        outputContainer["skip"] = False #default
        stepDict["output"].append(outputContainer)
    if "commands" in stepDict:
        for i,command in enumerate(stepDict["commands"]):
            enrichOutputContainer(i,command)
    else:
        enrichOutputContainer(0,"")

def _setHostfileAttributes(stepDict,hostDict):
    hostReferenceName = stepDict["name"].split(" ")[0]
    logging.debug('checking hostReferenceName {}'.format(hostReferenceName))
    hostDictEntry = _isInDictionary(hostReferenceName,hostDict,None)
    #if hostDictEntry:
    #    pass
    #else:
    #    if "device" in stepDict.keys():
    #        if stepDict["device"] == "local-shell":
    #            pass
    #        else:
    #            logging.warning ("host-dict lookup failed for step: {} device:{}".format(stepDict["name"],stepDict["device"]))
    stepDict["hostname"] = ""
    if hostDictEntry:
        stepDict["hostname"] = hostReferenceName
        stepDict["device"] = hostDictEntry["device"]
        for dictKey in hostDictEntry.keys():
            if dictKey not in stepDict:
                if dictKey in hostDictEntry.keys(): stepDict[dictKey] = hostDictEntry[dictKey]
