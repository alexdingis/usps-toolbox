##
## This script is to delete all of the fields that begin with "Count_" in an attribute table
## It may be occassionally necessary to delete everything
##
import arcpy
theFeatureClass = "Tool_Test_Tracts_01"
featFields      = arcpy.ListFields(theFeatureClass)
delFlds         = [item.name for item in featFields if item.name[:6].upper() == 'COUNT_']
arcpy.DeleteField_management(theFeatureClass,delFlds)
del theFeatureClass, featFields, delFlds, item
##