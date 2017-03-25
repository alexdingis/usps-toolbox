##
##
import arcpy, time, numpy, os, csv
## workspace here is where the usps tables are, maybe it should be deleted at the end of the script?
## if the user has the workspace set, maybe make a variable of that, set this workspace to be temporary then at the end of the script set the workspace back to the old one?
## thoughts?
workspace                 = arcpy.GetParameterAsText(0) #SP# first input of the tool
arcpy.env.workspace       = workspace
arcpy.env.overwriteOutput = True
##
##
##theFeatureClass is the project geography of census tracts
##
theFeatureClass           = arcpy.GetParameterAsText(1)
analysisFeatureClass      = theFeatureClass
##
## if the checkBox is  true, we want to output a new feature class then perform the operations on the output
## if the checkBox is false, we want to perform the operations to theFeatureClass
##
##
isChecked = arcpy.GetParameterAsText(2) ## the checkbox itself
##
##
#if (str(isChecked)) == 'true':
#	##
#	## the out path is the location of the new output feature class
#	## the analysisFeatureClass is the new output feature class
#	## then the tool will perform the new feature class function
#	##
#	arcpy.AddMessage("The check box was checked")
#	out_path             = GetParameterAsText(3)
#	analysisFeatureClass = GetParameterAsText(4)
#	arcpy.FeatureClassToFeatureClassConversion(theFeatureClass,out_path, analysisFeatureClass)
#else:
#	##
#	## if it's not checked, then theFeatureClass just becomes the analysisFeatureClass
#	##
#	analysisFeatureClass = theFeatureClass
##
##
##
## these are the fields that are extracted -- residential count, residential vacancy county, and residential vacant less than 3 months count
#SP# should we discuss having an output shapefile instead of writing over the originial input?
#AD#
#SP# arcpy.env.overwriteOutput = True #this will allow us to run the tool multiple times on the same datasets and just overwrite the results, it would be useful if we can figure out how to dynamically update the source datasets
#AD# this on line 9
theCalculations           = [["ams_res", "SUM"], ["res_vac", "SUM"],["vac_3_res", "SUM"]]
newTables                 = []
start_time                = time.time()
myList                    = []
##
## this uses a search cursor to make a list of all the geoids in the target census tracts then does a selection on each
## this really helps speed up the process even if the selection is a couple hundred or even thousand
## because otherwise it has to run the analysis on something like 78,000 records
##
with arcpy.da.SearchCursor(analysisFeatureClass, ("GEOID")) as cursor:
    for row in cursor:
        if str(row[0]) not in myList:
            myList.append(str(row[0]))
del row
del cursor
##
## I struggled with this and had to ask the internet, I'm not an expert on the part below
## either way, sql_query works to query the data
##
geoid_field = arcpy.AddFieldDelimiters(analysisFeatureClass, "GEOID")
myTuple = tuple(myList)
sql_query = "{0} IN {1}".format(geoid_field, myTuple)
##
##
## gets a list of the tables in the workspace then sorts them
tables = arcpy.ListTables()
tables.sort()
for table in tables:
## checks if the table starts as "usps_" which it should
	if table[:5].upper() == "USPS_":
		print "now working on: " + str(table)
		## a table view to run the analysis
		tblView = "table_view" + table[-8:]
		arcpy.MakeTableView_management(table, tblView)
		arcpy.SelectLayerByAttribute_management(tblView, "ADD_TO_SELECTION", sql_query)
		outTable = tblView + "_SUMSTAT"
		newTables.append(outTable)
		arcpy.Statistics_analysis(tblView, outTable, theCalculations, "geoid")
## deleting the tblView used to work but now it the script and I am not sure what changed
## this was to help delete all the excess that gets generated
		##arcpy.Delete_management(tblView)
		arcpy.SelectLayerByAttribute_management(tblView,"CLEAR_SELECTION")
newTables.sort()
for newTable in newTables:
	## prepares naming conventions for new fields
	newTableEnd        = (newTable[10:-8])
	Count_Res          = "Count_Res"       + newTableEnd
	Count_Res_Vac      = "Count_Res_Vac"   + newTableEnd
	Count_Vac_3_Mos    = "Count_Vac_3_Mos" + newTableEnd
	Count_Rec_Mail     = "Count_Rec_Mail"  + newTableEnd
	Count_Rec_Mail_Expression = "!" + Count_Res + "! - !" + Count_Res_Vac + "!"
	## adds new fields so they fit a naming convention
	arcpy.AddField_management(newTable, Count_Res, "LONG")
	arcpy.AddField_management(newTable, Count_Res_Vac, "LONG")
	arcpy.AddField_management(newTable, Count_Vac_3_Mos, "LONG")
	arcpy.AddField_management(newTable, Count_Rec_Mail, "LONG")
	## calculates the fields
	arcpy.CalculateField_management(newTable, Count_Res, "!SUM_ams_res!","PYTHON_9.3")
	arcpy.CalculateField_management(newTable, Count_Res_Vac, "!SUM_res_vac!","PYTHON_9.3")
	arcpy.CalculateField_management(newTable, Count_Vac_3_Mos, "!SUM_vac_3_res!","PYTHON_9.3")
	arcpy.CalculateField_management(newTable, Count_Rec_Mail, Count_Rec_Mail_Expression, "PYTHON_9.3")
	## deletes excess fields
	arcpy.DeleteField_management(newTable,["FREQUENCY","SUM_ams_res","SUM_res_vac","SUM_vac_3_res"])
	## joins the fields
	arcpy.JoinField_management(analysisFeatureClass,"GEOID",newTable,"GEOID")
##
## this is a pythonic statement to delete a bunch of excess geoid fields except the original one which you want to keep
##
flds = [fld.name for fld in arcpy.ListFields(analysisFeatureClass) if ((fld.name)[:5]).upper() == "GEOID" and len(fld.name) > 5]
arcpy.DeleteField_management(analysisFeatureClass,flds)
##
## this deletes some of the tables
##
for newTable in newTables:
	desc    = arcpy.Describe(newTable)
	catPath = desc.catalogPath
	arcpy.Delete_management(catPath)
print("Done setting up the attribute table: --- %s seconds ---" % round(time.time() - start_time, 2))
##


## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## this is for getting the sums of each field
columnTypes = ["Count_Res_2", "Count_Res_V", "Count_Vac_3", "Count_Rec_M"]
fields          = arcpy.ListFields(analysisFeatureClass)
for column in columnTypes:
	for field in fields:
		if field.name[:11] == column:
			fld = field.name
			feeled = arcpy.da.TableToNumPyArray (analysisFeatureClass, fld, skip_nulls=True)
			sum = feeled[fld].sum()
			print str(field.name) + " | " + str(sum)
print("Done printing: --- %s seconds ---" % round(time.time() - start_time, 2))


## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
## this will print out a CSV describing the overall data set (or if you have a selection/def query on, that) for each category for each quarter
## the name of the output CSV then the output directory
## maybe the directory should be reset after the script is executed?
myCSV           = "test_01"
thisDir         = "C:\Users\Alexander\Desktop\School\Projects\Louisiana_USPS_2017_01\Output"
fields          = arcpy.ListFields(analysisFeatureClass)
listResCount    = []
listResVacCount = []
listVac3Mos     = []
listRecMail     = []
os.chdir(thisDir)
##
## looks to see if the column in the attribute table starts a certain way
## then goes through each field to see if they look that way
## if the field.name matches the column it will do an if/elif
## then generate a sum
##
columnTypes = ["Count_Res_2", "Count_Res_V", "Count_Vac_3", "Count_Rec_M"]
for column in columnTypes:
	for field in fields:
		if field.name[:11] == column:
			if column == "Count_Res_2":
				fld = field.name
				feeled = arcpy.da.TableToNumPyArray (analysisFeatureClass, fld, skip_nulls=True)
				sum = feeled[fld].sum()
				listResCount.append(sum)
			elif column == "Count_Res_V":
				fld = field.name
				feeled = arcpy.da.TableToNumPyArray (analysisFeatureClass, fld, skip_nulls=True)
				sum = feeled[fld].sum()
				listResVacCount.append(sum)
			elif column == "Count_Vac_3":
				fld = field.name
				feeled = arcpy.da.TableToNumPyArray (analysisFeatureClass, fld, skip_nulls=True)
				sum = feeled[fld].sum()
				listVac3Mos.append(sum)
			elif column == "Count_Rec_M":
				fld = field.name
				feeled = arcpy.da.TableToNumPyArray (analysisFeatureClass, fld, skip_nulls=True)
				sum = feeled[fld].sum()
				listRecMail.append(sum)
##
## this prepends names to the lists for headers for the CSV
##
listResCount.insert(0,"Count of Residences")
listResVacCount.insert(0,"Count of Vacant Residences")
listVac3Mos.insert(0,"Count of Residences Vacant 3 Months or Less")
listRecMail.insert(0,"Count Residences Receiving Mail")
##
## this goes and gets the names of the fields for a list
##
quarterList = []
fields = arcpy.ListFields(analysisFeatureClass)
for field in fields:
	if field.name[-2:-1]  == "Q":
		if field.name[-7:] not in quarterList:
			quarterList.append(field.name[-7:])
quarterList.insert(0,"Quarter")
##
## this transposes the matrices of the lists because otherwise they print the wrong direction in the CSV
## python prints to rows in CSVs, not columns
##
rows1 = [quarterList, listResCount, listResVacCount, listVac3Mos, listRecMail]
rows2  = zip(*rows1)

## check that all lists have the same length
## I am not sure this was the best way to do this
##length = len(quarterList)
##if all(len(lst) == length for lst in [quarterList, listResCount, listResVacCount, listResVacCount, listRecMail]):
##	print len(quarterList), len(listResCount), len(listResVacCount), len(listResVacCount), len(listRecMail)
##
## this does the actual writing
##
with open(myCSV, 'wb') as f:
    writer = csv.writer(f)
    for row in rows2:
    	writer.writerow(row)
print("Done printing to csv: --- %s seconds ---" % round(time.time() - start_time, 2))

## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
del thisDir, fld, feeled, field, fields, column, columnTypes, listResCount, listResVacCount, listVac3Mos, listRecMail, quarterList, row, rows, writer, f
## ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
























