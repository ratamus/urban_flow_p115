# -*- coding: utf-8 -*-
# **************************** All rights reserved. Copyright (c) 2022 Lynker Analytics Ltd ****************************
# Author: Based off a script from Morphum - Rātā Chapman Olsen
# Date: 20/12/2022
# Functionality: adds a catchment area field to the streamline network. Assumes input is in meters.
# Version: 1.0 py3.9
# **********************************************************************************************************************
# standard module
import arcpy


# these top three variables need to be changed every time. The should be ok. A field is added to the stream table
arcpy.env.workspace = r'C:\Users\RataChapmanOlsen\Documents\ArcGIS\Projects\Urban flow\Urban flow.gdb'
# stream network created from dem
stream_lines = r"C:\Users\RataChapmanOlsen\Documents\ArcGIS\Projects\Urban flow\Urban flow.gdb\olfpv2_merge"
# flow accumulation raster which was used to create the stream network
flow_accumulation_raster = r"C:\Users\RataChapmanOlsen\Documents\ArcGIS\Projects\Urban flow\Urban flow.gdb\accumulationv2"
id_field = 'OBJECTID'  # 'FID'

# temp points table
mid_points = r"in_memory\xy_table_DS_Node_Points"
# copy the midpoints to disc
preserve_downstream_node_points = True

arcpy.env.overwriteOutput = True

arcpy.RepairGeometry_management(stream_lines, "DELETE_NULL", "OGC")

print('Calculating Downstream  Node Catchment Size...')
# create a primary key on the streamlines
arcpy.AddField_management(stream_lines, "arcid", "LONG", None, None, None, '', "NULLABLE", "NON_REQUIRED", '')
arcpy.CalculateField_management(stream_lines, "arcid", "!" + id_field + "!", "PYTHON3", '', "TEXT", "NO_ENFORCE_DOMAINS")

# create field and populate the midpoint of segment x y
arcpy.AddGeometryAttributes_management(stream_lines, "LINE_START_MID_END", "METERS", '', arcpy.SpatialReference(2193))

# create a points datasets for the midpoint
arcpy.XYTableToPoint_management(stream_lines, mid_points, "MID_X", "MID_Y", "#",
                                arcpy.SpatialReference(2193))

# extract the accumulation raster value at the midpoint and add it as a field to the points table
arcpy.sa.ExtractMultiValuesToPoints(mid_points,
                                    [[flow_accumulation_raster.strip("'"), "Catchment_Area_SQM"]], "NONE")

arcpy.AddField_management(mid_points, "ca_area_ha", "DOUBLE", None, None, None, '', "NULLABLE", "NON_REQUIRED", '')
# divide the accumulation field by 10000 to get hectares
query = "(!Catchment_Area_SQM!)/10000"
arcpy.CalculateField_management(mid_points, "ca_area_ha", query, "PYTHON3", '')

# join the accumulation field onto to the line segments
arcpy.JoinField_management(stream_lines, "arcid", mid_points, "arcid", ["ca_area_ha", "Catchment_Area_SQM"])

# create a copy of the midpoints if needed
if preserve_downstream_node_points is True:
    arcpy.CopyFeatures_management(mid_points, "downstream_node_points")
else:
    pass

# tidy up fields
# arcpy.DeleteField_management(stream_lines, "arcid;END_X;END_Y;from_node;grid_code;MID_X;MID_Y;START_X;START_Y;to_node")
