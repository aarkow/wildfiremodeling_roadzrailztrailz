# -*- coding: utf-8 -*-
"""
Name: Roads Rails Trails Input Processing Wildfire Treatment Outcome Modeling

Authors:
Alex Arkowitz @ USFS RMRS & Colorado State University - alexander.arkowitz@colostate.edu , alex.arkowitz@usda.gov
Leo Oniell @ USFS - christopher.oneill@usda.gov
Date Created: 03/08/2024

Limitations: Only to be used with ArcGIS Pro 3.X as a python 3 script that only works with a ArcGIS Toolbox. The toolbox found in this directory will provide the necessary parameters needed to run the tool.

Usage: This tool is to be run when roads trails and rails are needed to analyze their effects on wildfire containment. 

Description: This tool takes USGS transportation features, as well as USFS core road data, and processes them to remove duplicates. This includes a process to remove "nearly identical" roads (lines) that USGS and USFS roads layers contain.
USGS and USFS roads have different lines with slightly different vertices that represent the same road. This script removes exact duplicates, and then uses a X (default in tool is currently 50) meter buffer to remove these duplicates.
Often this buffered clip of USFS roads still leaves small sections of line that falls right outside of the buffer and therefor, a query identifies line segments in the clipped USFS roads layer that are smaller than 100m and deletes them.
Width for roads and trails will need to be updated by users. For this script, the width was calculated using randomly sampled sections of line to calculate a rounded mean width.

User Preprocessing:
User needs to provide fire perimeter or AOI polygon
USFS Road data needs to be downloaded locally: https://data.fs.usda.gov/geodata/edw/datasets.php?xmlKeyword=roadcore
USGS Trails Rails and Roads needs to be downloaded from here: https://apps.nationalmap.gov/downloader/         > Transportation > File Geodatabse
*Make sure these inputs use the same coordinate system
"""

###Import Libraries###
import arcpy, os, sys, traceback
from sys import argv
from datetime import datetime, timezone
from arcpy import metadata as md

###Arcgis Pro Tool User Input Parameters###
userfireperimeters = arcpy.GetParameter(0) # Feature Set: Input parameter for user-provided fire perimeters #Required
USGS_RailFeature = arcpy.GetParameter(1) # Feature Set: Input parameter for user-provided USGS Trans rail line type #Required
USGS_TrailSegment = arcpy.GetParameter(2) # Feature Set: Input parameter for user-provided USGS Trans trail line type #Required
USGS_RoadSegment = arcpy.GetParameter(3) # Feature Set: Input parameter for user-provided USGS Trans Road line type #Required
RoadCore_FS = arcpy.GetParameter(4) # Feature Set: Input parameter for user-provided USFS Roads Core line type #Required
USFS_Road_Buff = arcpy.GetParameterAsText(5) # String value to buffer USGS roads to delete similar USFS roads that represent the same roads but have slightly similar vertices.
USFS_RoadLineLengthToDel = arcpy.GetParameterAsText(6) # String value to erase small sections of road that buffer/erase left behind

###Variables###
try:
    # Grab & Format system date & time
    dt = datetime.now()
    datetime = dt.strftime("%Y%m%d_%H%M")
    #PC Directory
    scrptfolder = os.path.dirname(__file__) #Returns the UNC of the folder where this python file sits
    folder_lst = os.path.split(scrptfolder) #make a list of the head and tail of the scripts folder
    local_root_fld = folder_lst[0] #Access the head (full directory) where the scripts folder resides
    #GDB
    output_fgdb = os.path.join(local_root_fld,"data","output.gdb")
    input_fgdb = os.path.join(local_root_fld,"data","input.gdb")
    scratchworkspace = os.path.join(local_root_fld,"processing","interim.gdb")

except:
    arcpy.AddError("Variables could not be set. Exiting...")
    print("Variables could not be set. Exiting...")
    sys.exit()

###Environment Settings###
try:
    # To allow overwriting outputs change overwriteOutput option to True.
    arcpy.env.overwriteOutput = True
    # Environment settings
    arcpy.env.workspace = scratchworkspace
except:
    arcpy.AddError("Evironments could not be set. Exiting...")
    print("Evironments could not be set. Exiting...")
    sys.exit()

###Functions###
#Function to report any errors that occur in the IDLE or ArcPro Tool message screen
def report_error():   
    # Get the traceback object
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    # Concatenate information together concerning the error into a message string
    pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
    msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
    # Return python error messages for use in script tool or Python Window
    arcpy.AddMessage(pymsg)
    arcpy.AddMessage(msgs)
    print(pymsg)
    print(msgs)    

###Start Script###
try:

    #Get inc name from input perimeter to attribute to output name
    if arcpy.Exists(userfireperimeters):
        with arcpy.da.SearchCursor(userfireperimeters, "attr_IncidentName") as cursor:
            for row in cursor:
                IncName=row[0]
                break
        IncName = IncName.replace(" ","")
        arcpy.AddMessage("Incident named: "+IncName)
    else:
        arcpy.AddError("Input perimeter not found")


    
    arcpy.AddMessage("Buffering Perimeters to ID AOI")
    #Buffer fires to designate AOI
    arcpy.analysis.PairwiseBuffer(userfireperimeters,"Perims_10kmBuff","1 Kilometers","ALL",None,"GEODESIC","0 DecimalDegrees")

    #Delete transit features based on attribution
        #USFS roads did not need filtering, it was all road.
        #USGS Rails did not need filtering, it was all rail.
        #USGS roads we will need to delete "Ferry Routes" and "Tunnel" which are TNMFRC codes 7 and 8
    arcpy.management.MakeFeatureLayer(USGS_RoadSegment,"usgs_trans_road_tnl_wtr","tnmfrc IN (7, 8)",None)
    arcpy.management.DeleteFeatures("usgs_trans_road_tnl_wtr")
        #USGS trails will delete Trail type = Water Trail
    arcpy.management.MakeFeatureLayer(USGS_TrailSegment,"usgs_trans_trail_water","trailtype LIKE '%Water%'",None)
    arcpy.management.DeleteFeatures("usgs_trans_trail_water")

    arcpy.AddMessage("Clipping Transportation layers to AOI")
    #Clip all trans data to this AOI
    arcpy.analysis.PairwiseClip(USGS_RailFeature,"Perims_10kmBuff","AOIClp_RailFeature")
    arcpy.analysis.PairwiseClip(USGS_TrailSegment,"Perims_10kmBuff","AOIClp_TrailSegment")
    arcpy.analysis.PairwiseClip(USGS_RoadSegment,"Perims_10kmBuff","AOIClp_RoadSegment")
    arcpy.analysis.PairwiseClip(RoadCore_FS,"Perims_10kmBuff","AOI_Clp_RoadCore_FS")

    arcpy.AddMessage("Identifying and deleting exact duplicates")
    #Intersect USGS Trails and roads to ID areas of exact overlap
    arcpy.analysis.PairwiseIntersect("AOIClp_RoadSegment;AOIClp_TrailSegment","USGS_Trails_Roads_Intersect","ONLY_FID",None,"INPUT")
    #Erase areas of intersect from trails. Erased from trails as roads take priority.
    arcpy.analysis.PairwiseErase("AOIClp_TrailSegment","USGS_Trails_Roads_Intersect","AOI_Clp_Trails_RoadsErased",None)

    #Merge USGS roads and trails as the intersection in next step only allows 2 features
    arcpy.management.Merge("AOIClp_RoadSegment;AOI_Clp_Trails_RoadsErased","USGS_TrailsRoads_Mrg",'permanent_identifier "Permanent_Identifier" true true false 40 Text 0 0,First,#,AOIClp_RoadSegment,permanent_identifier,0,40',"NO_SOURCE_INFO")

    #Intersect USGS trails and roads (merged above) with USFS roads to remove exact duplicates
    arcpy.analysis.PairwiseIntersect("USGS_TrailsRoads_Mrg;AOI_Clp_RoadCore_FS","USGS_USFS_TransInt","ONLY_FID",None,"INPUT")
    #Erase areas of intersect from trails. Erased from USFS as USGS roads take priority as the more authoritative dataset
    arcpy.analysis.PairwiseErase("AOI_Clp_RoadCore_FS","USGS_USFS_TransInt","USFS_Roads_USGS_Erased")

    arcpy.AddMessage("Repairing geometry")
    #Repair geometry on both processed features
    arcpy.management.RepairGeometry("AOI_Clp_Trails_RoadsErased","DELETE_NULL","ESRI")
    arcpy.management.RepairGeometry("USFS_Roads_USGS_Erased","DELETE_NULL","ESRI")

    ''' 
    We now have:
    AOIClp_RailFeature:USGS Rails with no processing done other than clipping to AOI
    AOIClp_RoadSegment: USGS Roads with no processing done other than clipping to AOI
    AOI_Clp_Trails_RoadsErased: USGS trails that do not share same geometry as roads
    USFS_Roads_USGS_Erased: USFS roads that dont share the same exact geometry with USGS trails and USGS roads

    At this point we have removed half of USFS roads, but tons of "duplicates" that contain slightly different verticis still exist between USGS roads and USGS trans . 

    Question to review later: Do feature classes have duplicates within the FC itself? This may effect model influence so we may need to dissove roads on select fields.
    '''
    arcpy.AddMessage("Removing USFS roads that have similar geometry in USGS data using a "+USFS_Road_Buff+" meter buffer")
    #To remove USFS roads that have nearly the same geometry, we must merge all USGS trans data, create a buffer, and then erase from USFS roads.
    arcpy.management.Merge("AOI_Clp_Trails_RoadsErased;AOIClp_RoadSegment;AOIClp_RailFeature","USGS_AllMrg")
    arcpy.analysis.PairwiseBuffer("USGS_AllMrg","USGS_AllMrg_Buffer",str(USFS_Road_Buff)+" Meters","ALL",None,"GEODESIC","0 DecimalDegrees")

    #Clean up workspace/delete interim processing data so that erase has a chance to work on fed comp
    fc_Delete = ["Perims_10kmBuff","USGS_Trails_Roads_Intersect","USGS_TrailsRoads_Mrg","AOIClp_TrailSegment","USGS_USFS_TransInt"]
    for fc in fc_Delete:
        fc_path = os.path.join(scratchworkspace, fc)
        if arcpy.Exists(fc_path):
            arcpy.Delete_management(fc_path) 


    #Erase this buffer from USFS roads. Unfortunately we will lose buff distance of USFS roads that are not duplicates due to buffer, but other ways explored did not work.
    #Note: Alex's fed comp did not run this well. In fact... it made a screen give out and froze the whole thing after showing a bunch of warning messages. You can run this on different sections of the AOI and merge later.
    arcpy.analysis.PairwiseErase("USFS_Roads_USGS_Erased","USGS_AllMrg_Buffer","USFS_Roads_USGS_EraseBuff")

    #Several small segments that fell outside of buffer still present. This next section of code will delete line segments <100m
    arcpy.management.AddField("USFS_Roads_USGS_EraseBuff","LineLength","DOUBLE",None,None,None,"","NULLABLE","NON_REQUIRED","")
    arcpy.management.CalculateGeometryAttributes("USFS_Roads_USGS_EraseBuff","LineLength LENGTH_GEODESIC","METERS","",None,"SAME_AS_INPUT")
    arcpy.management.MakeFeatureLayer("USFS_Roads_USGS_EraseBuff","USFS_Roads_USGS_EraseBuff_SmallLinesToDelete","LineLength < "+str(USFS_RoadLineLengthToDel))
    arcpy.management.DeleteFeatures("USFS_Roads_USGS_EraseBuff_SmallLinesToDelete")

    #Clean up workspace/delete interim processing data
    fc_Delete = ["Perims_10kmBuff","USGS_Trails_Roads_Intersect","USGS_TrailsRoads_Mrg","USGS_AllMrg","USGS_AllMrg_Buffer","AOI_Clp_RoadCore_FS","AOIClp_TrailSegment","USGS_USFS_TransInt","USFS_Roads_USGS_Erased"]
    for fc in fc_Delete:
        fc_path = os.path.join(scratchworkspace, fc)
        if arcpy.Exists(fc_path):
            arcpy.Delete_management(fc_path) 
except:
    arcpy.AddError("Error Preprocessing. Exiting.")
    print("Error Preprocessing. Exiting.")
    #Clean up workspace/delete interim processing data
    fc_Delete = ["Perims_10kmBuff","USGS_Trails_Roads_Intersect","USGS_TrailsRoads_Mrg","USGS_AllMrg","USGS_AllMrg_Buffer","AOI_Clp_RoadCore_FS","AOIClp_TrailSegment","USGS_USFS_TransInt","USFS_Roads_USGS_Erased","AOI_Clp_Trails_RoadsErased","AOIClp_RailFeature","AOIClp_RoadSegment","USFS_Roads_USGS_EraseBuff"]
    for fc in fc_Delete:
        fc_path = os.path.join(scratchworkspace, fc)
        if arcpy.Exists(fc_path):
            arcpy.Delete_management(fc_path) 
    report_error()
    sys.exit()


#This next section attributes a width to line segments and merges the output into one feature class that can be found in the output folder.
try:
    #Dissolve the data based on the only field we care about, that will be used to attribute width. This will also remove overlapping duplicates.
    arcpy.analysis.PairwiseDissolve("AOIClp_RoadSegment","AOIClp_USGS_Road_TNMFRC_Diss","tnmfrc",None,"MULTI_PART","")
    ####Attribute Width to USGS Roads
    arcpy.management.CalculateField("AOIClp_USGS_Road_TNMFRC_Diss","Width","Reclass(!tnmfrc!)","PYTHON3",
        code_block="""def Reclass(tnmfrc):
        if tnmfrc == 1:
            return 25
        elif tnmfrc == 2:
            return 20
        elif tnmfrc == 3:
            return 15
        elif tnmfrc == 4:
            return 5
        elif tnmfrc == 5:
            return 25
        elif tnmfrc == 6:
            return 3
        elif tnmfrc == 9:
            return 2
        elif tnmfrc is None:
            return None
        else: 
            return 1000""",
        field_type="DOUBLE",enforce_domains="NO_ENFORCE_DOMAINS")

    #Now for USFS roads create a new simplified field containing just a number for lane width
    arcpy.management.CalculateField("USFS_Roads_USGS_EraseBuff","LaneWidth","rcls(!LANES!)","PYTHON3",
    """def rcls(lanes):
    for char in str(lanes):
        if char.isdigit():
            return char
        else:
            return None""","TEXT","NO_ENFORCE_DOMAINS")
    #Dissolve only based on lane width for simplified dataset
    arcpy.analysis.PairwiseDissolve("USFS_Roads_USGS_EraseBuff","USFS_Roads_Diss_ALL","LaneWidth",None,"MULTI_PART","")

    
    ####Attribute width to USFS roads
    arcpy.management.CalculateField("USFS_Roads_Diss_ALL","Width","Reclass(!LaneWidth!)","PYTHON3","""def Reclass(LaneWidth):
    if LaneWidth == "1":
        return 5
    elif LaneWidth == "2":
        return 8
    elif LaneWidth == "3":
        return 10
    elif LaneWidth == "4":
        return 15
    elif LaneWidth == "5":
        return 25
    elif LaneWidth is None:
        return 5
    else: 
        return 1000""","DOUBLE","NO_ENFORCE_DOMAINS")
    ####Attribute width to USGS rail
    arcpy.management.CalculateField("AOIClp_RailFeature","Width","8","PYTHON3","","DOUBLE","NO_ENFORCE_DOMAINS")
    arcpy.analysis.PairwiseDissolve("AOIClp_RailFeature","AOIClp_Rail_Diss","Width",None,"MULTI_PART","")

    #TRAILS
    arcpy.management.AddField("AOI_Clp_Trails_RoadsErased","Width","DOUBLE",None,None,None,"","NULLABLE","NON_REQUIRED","")
    ####Attribute width to USGS trail
    arcpy.management.CalculateField("AOI_Clp_Trails_RoadsErased","Width","Reclass(!ohvover50inches!)","PYTHON3","""def Reclass(ohvover50inches):
        if ohvover50inches == "Y":
            return 1.5
        elif ohvover50inches is None:
            return 0.5
        else: 
            return 0.5""","TEXT","NO_ENFORCE_DOMAINS")

    arcpy.analysis.PairwiseDissolve("AOI_Clp_Trails_RoadsErased","AOI_Clp_Trails_Diss","Width",None,"MULTI_PART","")
    #Caculate field to track data source
    arcpy.management.CalculateField("AOIClp_Rail_Diss","Source",'"USGS_Rail"',"PYTHON3","","TEXT","NO_ENFORCE_DOMAINS")
    arcpy.management.CalculateField("AOI_Clp_Trails_Diss","Source",'"USGS_Trail"',"PYTHON3","","TEXT","NO_ENFORCE_DOMAINS")
    arcpy.management.CalculateField("AOIClp_USGS_Road_TNMFRC_Diss","Source",'"USGS_Road"',"PYTHON3","","TEXT","NO_ENFORCE_DOMAINS")
    arcpy.management.CalculateField("USFS_Roads_Diss_ALL","Source",'"USFS_Road"',"PYTHON3","","TEXT","NO_ENFORCE_DOMAINS")
    #Merge and dissolve and put it in output gdb
    arcpy.management.Merge("USFS_Roads_Diss_ALL;AOIClp_USGS_Road_TNMFRC_Diss;AOI_Clp_Trails_Diss;AOIClp_Rail_Diss","trans_usgs_usfs_containment",'Width "Width" true true false 8 Double 0 0,First,#,USFS_Roads_Diss_ALL,Width,-1,-1,AOIClp_USGS_Road_TNMFRC_Diss,Width,-1,-1,AOI_Clp_Trails_Diss,Width,-1,-1,AOIClp_Rail_Diss,Width,-1,-1;Source "Source" true true false 512 Text 0 0,First,#,USFS_Roads_Diss_ALL,Source,0,512,AOIClp_USGS_Road_TNMFRC_Diss,Source,0,512,AOI_Clp_Trails_Diss,Source,0,512,AOIClp_Rail_Diss,Source,0,512',"NO_SOURCE_INFO")
    arcpy.analysis.PairwiseDissolve("trans_usgs_usfs_containment",(os.path.join(output_fgdb,"transprtn_cntmnt_"+IncName+"_"+datetime)),"Source;Width",None,"MULTI_PART","")

    #Clean up workspace/delete interim processing data
    fc_Delete = ["AOI_Clp_Trails_Diss","AOI_Clp_Trails_RoadsErased","AOIClp_Rail_Diss","AOIClp_RailFeature","AOIClp_RoadSegment","AOIClp_USGS_Road_TNMFRC_Diss","USFS_Roads_Diss_ALL","USFS_Roads_USGS_EraseBuff"]
    for fc in fc_Delete:
        fc_path = os.path.join(scratchworkspace, fc)
        if arcpy.Exists(fc_path):
            arcpy.Delete_management(fc_path) 
    #"trans_usgs_usfs_containment"
    arcpy.AddMessage("Script Finished Running, Output located here: "+str(os.path.join(output_fgdb,"trans_usgs_usfs_containment_"+datetime)))
    
except:
    arcpy.AddError("Error Attributing Width. Exiting.")
    print("Error Attributing Width. Exiting.")
    #Clean up workspace/delete interim processing data
    fc_Delete = ["AOI_Clp_Trails_Diss","AOI_Clp_Trails_RoadsErased","AOIClp_Rail_Diss","AOIClp_RailFeature","AOIClp_RoadSegment","AOIClp_USGS_Road_TNMFRC_Diss","trans_usgs_usfs_containment","USFS_Roads_Diss_ALL","USFS_Roads_USGS_EraseBuff"]
    for fc in fc_Delete:
        fc_path = os.path.join(scratchworkspace, fc)
        if arcpy.Exists(fc_path):
            arcpy.Delete_management(fc_path) 
    report_error()
    sys.exit()
