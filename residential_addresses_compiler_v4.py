##
## Residential Address Compiler Version 4
## Alex Din and Sid Pandey
## For use in the ArcGIS environment
## The purpose of this tool is to transform tabular residential address data provided by the USPS and HUD for use in a GIS format
##
## Import the necessary
##
import arcpy, time, numpy
arcpy.env.overwriteOutput = True
##
## Set variables
##
uspsGDBLocation           = arcpy.GetParameterAsText(0)
theFeatureClass           = arcpy.GetParameterAsText(1)
isCheckedNewFC            = arcpy.GetParameterAsText(2)
newFCName                 = arcpy.GetParameterAsText(3)
out_path                  = arcpy.GetParameterAsText(4)
##
## this checks whether the checkbox for creating a new feature class is checked 
## OR
## to use the initial project geography
##
if (str(isCheckedNewFC)) == 'True':
	analysisFeatureClass  = newFCName
	arcpy.FeatureClassToFeatureClass_conversion(theFeatureClass,out_path, analysisFeatureClass)
else:
	analysisFeatureClass  = theFeatureClass
##
## This saves the current workspace as a variable then sets the workspace to the location of USPS DBFs GDB
##
currentWorkspace    = arcpy.env.workspace
arcpy.env.workspace = uspsGDBLocation
##
## These are the variables that data are pulled from
##
theCalculations  = [["ams_res", "SUM"], ["res_vac", "SUM"],["vac_3_res", "SUM"]]
newTables        = []
start_time       = time.time()
myList           = []
##
## This gets a list of the GEOIDs in the project geography
## It may be worth eventually doing a check to make sure the GEOID field 1) exists and 2) is the correct length (therefore, census tracts)
##
with arcpy.da.SearchCursor(analysisFeatureClass, ("GEOID")) as cursor:
	for row in cursor:
	    if str(row[0]) not in myList:
	        myList.append(str(row[0]))
del row, cursor
##
## This takes the list of GEOIDs from project geography and creates a selection statement to only pull those GEOIDs from the USPS DBFs
## Otherwise, you'd have to run the tool on 77,000+ census tract GEOIDs rather than the project area
##
geoid_field = arcpy.AddFieldDelimiters(analysisFeatureClass, "GEOID")
myTuple     = tuple(myList)
sql_query   = "{0} IN {1}".format(geoid_field, myTuple)
tables      = arcpy.ListTables()
tables.sort()
for table in tables:
## checks if the table starts as "usps_" which it should
	if table[:5].upper() == "USPS_":
		## a table view to run the analysis
		tblView  = "table_view" + table[-8:]
		arcpy.MakeTableView_management(table, tblView)
		arcpy.SelectLayerByAttribute_management(tblView, "ADD_TO_SELECTION", sql_query)
		outTable = tblView + "_SUMSTAT"
		newTables.append(outTable)
		arcpy.Statistics_analysis(tblView, outTable, theCalculations, "geoid")
		##arcpy.Delete_management(tblView)
		arcpy.SelectLayerByAttribute_management(tblView,"CLEAR_SELECTION")
newTables.sort()
for newTable in newTables:
	## prepares naming conventions for new fields
	newTableEnd               = (newTable[10:-8])
	Count_Res                 = "Count_Res%s"       %(newTableEnd)
	Count_Res_Vac             = "Count_Res_Vac%s"   %(newTableEnd)
	Count_Vac_3_Mos           = "Count_Vac_3_Mos%s" %(newTableEnd)
	Count_Rec_Mail            = "Count_Rec_Mail%s"  %(newTableEnd)
	Count_Rec_Mail_Expression = "!%s! - !%s!"       %(Count_Res, Count_Res_Vac)
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
## deletes excess fields again
flds    = [fld.name for fld in arcpy.ListFields(analysisFeatureClass) if ((fld.name)[:5]).upper() == "GEOID" and len(fld.name) > 5]
arcpy.DeleteField_management(analysisFeatureClass,flds)
## deletes excess tables
for newTable in newTables:
	desc    = arcpy.Describe(newTable)
	catPath = desc.catalogPath
	arcpy.Delete_management(catPath)
## delete the excess tables (method 2)
mxd = arcpy.mapping.MapDocument('current')
for table in arcpy.mapping.ListTableViews(mxd):
	if (table.name[:12]).upper() == "TABLE_VIEW_2":
		arcpy.Delete_management(table.name)
## returns the workspace to where the user had it
arcpy.env.workspace = currentWorkspace
##
print("Done setting up the attribute table: --- %s seconds ---" % round(time.time() - start_time, 2))
##
##