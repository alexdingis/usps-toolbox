##
## Export Project Level CSV Version 1
## Alex Din and Sid Pandey
## For use in the ArcGIS environment
## The purpose of this tool is to export a CSV with information of the entire project geography
## Each record is a quarter
##
## Import the necessary
##
import arcpy, time, numpy, os, csv
arcpy.env.overwriteOutput = True
##
##
##
analysisFeatureClass      = arcpy.GetParameterAsText(1)
exportCSVName             = arcpy.GetParameterAsText(1)
csvOutputDirectory        = arcpy.GetParameterAsText(2)
##
##
##
start_time      = time.time()
myCSV           = "%s.csv" %(exportCSVName)
thisDir         = csvOutputDirectory
fields          = arcpy.ListFields(analysisFeatureClass)
listResCount    = []
listResVacCount = []
listVac3Mos     = []
listRecMail     = []
os.chdir(thisDir)
##
columnTypes     = ["Count_Res_2", "Count_Res_V", "Count_Vac_3", "Count_Rec_M"]
for column in columnTypes:
	for field in fields:
		if field.name[:11] == column:
			if column      == "Count_Res_2":
				fld         = field.name
				feeled      = arcpy.da.TableToNumPyArray (analysisFeatureClass, fld, skip_nulls=True)
				sum         = feeled[fld].sum()
				listResCount.append(sum)
			elif column    == "Count_Res_V":
				fld         = field.name
				feeled      = arcpy.da.TableToNumPyArray (analysisFeatureClass, fld, skip_nulls=True)
				sum         = feeled[fld].sum()
				listResVacCount.append(sum)
			elif column    == "Count_Vac_3":
				fld         = field.name
				feeled      = arcpy.da.TableToNumPyArray (analysisFeatureClass, fld, skip_nulls=True)
				sum         = feeled[fld].sum()
				listVac3Mos.append(sum)
			elif column    == "Count_Rec_M":
				fld         = field.name
				feeled      = arcpy.da.TableToNumPyArray (analysisFeatureClass, fld, skip_nulls=True)
				sum         = feeled[fld].sum()
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
fields      = arcpy.ListFields(analysisFeatureClass)
for field in fields:
	if field.name[-2:-1]  == "Q":
		if field.name[-7:] not in quarterList:
			quarterList.append(field.name[-7:])
quarterList.insert(0,"Quarter")
##
## this transposes the matrices of the lists because otherwise they print the wrong direction in the CSV
## python prints to rows in CSVs, not columns
##
rows1      = [quarterList, listResCount, listResVacCount, listVac3Mos, listRecMail]
rows2      = zip(*rows1)
with open(myCSV, 'wb') as f:
    writer = csv.writer(f)
    for row in rows2:
    	writer.writerow(row)
print("Done printing to csv: --- %s seconds ---" % round(time.time() - start_time, 2))
##
## --------------------------------------------------
