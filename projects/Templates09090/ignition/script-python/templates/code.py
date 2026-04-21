def getActiveChildrenAlarms(tagPath):
	
	if tagPath!='':
		splitPath = tagPath.split(']')
		filter = ['*%s*' % splitPath[-1]]
			
		states = ['ActiveUnacked','ActiveAcked']
		activeAlarms = system.alarm.queryStatus(Path = filter,state = states)
		ret = []
		for alarm in activeAlarms:
			item = {
				'name': str(alarm.getName()),
				'state': str(alarm.getState())
			}
			ret.append(item)
	else:
		ret = []
	
	return ret

def getFaceplateTabs(tagPath):
		
	config = system.tag.getConfiguration(tagPath)
	typeId = config[0]['typeId']
	split = typeId.split('/')
	type = split[-1]
	
	icons = {
		
	}
	
	#getTabs
	#add more tabs here as needed to account for all templates, the below script will only use the present folders
	tabOrder = [
		{'type':'Control','order':0},
		{'type':'Engineering','order':1},
		{'type':'Maintenance','order':2},
		{'type':'Alarming','order':3}
	]
	tabs = []
	results = system.tag.browse(tagPath)
	for result in results:
		browseType = str(result['fullPath'])
		splitChild = browseType.split('/')
		for tab in tabOrder:
			if tab['type']==splitChild[-1]:
				#default to selecting control
				tab['tabSelection'] = 0
				tab['tagPath'] = tagPath
				tabs.append(tab)
	
	#order list becuase python doesn't
	def orderElements(element):
		return element['order']
	tabs.sort(key=orderElements)
	
	return tabs

def getFacePlateAlarmList(tagPath):
	
	def unCamelCase(myStr):
		retStr = ""
		for x in range(len(myStr)):
			
			c = myStr[x]
			if c.isupper() and x != 0:
				retStr += " %s" % c
			else:
				retStr += c
		
		return retStr	

	alarms = []
	alarmTagPath = tagPath+'/Alarming'
	results = system.tag.browse(path = alarmTagPath, filter = {'tagType':'AtomicTag'})
	for result in results.getResults():
		results2 = system.tag.getConfiguration(result['fullPath'])
		#x = results2[0]['alarms']
		if 'alarms' in results2[0]:
			alarm = {
				'label': unCamelCase(result['name']),
				'status': result['value'].value
			}
			alarms.append(alarm)
	return alarms
	
def getTagValues(currentTime, tagPaths):
	
	timeDiff = abs(system.date.secondsBetween(system.date.now(),currentTime))

	if timeDiff>3:#historical
		startDate = system.date.addSeconds(currentTime,-1)
	
		tagPathsList = []
		tagAliases = []
		for item in tagPaths:
			
			#perform checks on tag to make sure it is ready to be queried
			exists = system.tag.exists(tagPaths[item])
			if exists:	
				quality = system.tag.read(tagPaths[item]).quality
				historized = system.tag.getConfiguration(tagPaths[item], False)[0]['historyEnabled']
					
				#check validity of tag
				if str(quality)=='Good' and historized:
					tagPathsList.append(tagPaths[item])
					tagAliases.append(item)
	
		tagData = system.tag.queryTagHistory(tagPathsList,startDate,currentTime,returnSize=1,aggregationMode="LastValue",returnFormat='Wide',columnNames=tagAliases)
		tagValues = {}
		for item in tagAliases:
			tagValues[item] = tagData.getValueAt(0,item)
		ret = tagValues
	else:#use realtime tags for the data
		tagPathsList = []
		tagAliases = []
		for item in tagPaths:
			#perform checks on tag to make sure it is ready to be queried
			exists = system.tag.exists(tagPaths[item])
			if exists:	
				
				quality = system.tag.read(tagPaths[item]).quality					
				#check validity of tag
				if str(quality)=='Good':
					tagPathsList.append(tagPaths[item])
					tagAliases.append(item)
		
		tagData = system.tag.readBlocking(tagPathsList)
		tagValues = {}
		i=0
		for item in tagAliases:
			tagValues[item] = tagData[i].value
			i+=1
		ret = tagValues
				
	return ret
	
