import arcpy
from arcpy import env
from arcpy.sa import *


def printme(text):
    print(text)
    arcpy.AddMessage(text)


''' Tool Environments ''' 
arcpy.env.workspace = arcpy.GetParameterAsText(0)
# arcpy.env.snapRaster = raw_dem
# arcpy.env.extent = raw_dem

# ''' Tool Parameters '''
# iteration = arcpy.GetParameterAsText(3) # Iteration number refers to the iteration number each time the model is run
# iteration = '_' + iteration
# iteration = '' #iteration number disabled for Initial Stream Delineation script as not required.

# dataset_code = arcpy.GetParameterAsText(4)
# dataset_code = dataset_code + '_'

stream_threshold = arcpy.GetParameterAsText(1)  # Variable sets the number of cells that must flow through a cell to define the 'river threshold'
# stream_threshold_filename_ext = '_' + str(round(int(stream_threshold)/1000)) + 'k' # variable used to append to stream features filename
stream_threshold_list = stream_threshold.split(',')

depression_threshold = arcpy.GetParameterAsText(2)  # Default is 0.05 (50mm)

''' Tool Outputs'''
create_vector_OLFP = arcpy.GetParameter(3)
create_depressions = arcpy.GetParameter(4)

'''input Data'''
flow_accumulation_raster = arcpy.GetParameterAsText(5)
flow_direction_raster = arcpy.GetParameterAsText(6)
depression_raster = arcpy.GetParameterAsText(7)

'''Intermediate Data'''
setNull_raster = "setNullRaster_test"
streamOrder_raster = 'streamOrderRast'
intRaster = 'intRaster'
rasterPoints = 'rasterPoints'
rasterPoints_Depth = 'rasterPoints_Depth'
depressions_Polygon = 'Depressions_Poly'

'''Output Data'''
OLFP_Order_Polyline = 'OLFP_StreamOrder'
depressions_Polygons_Filtered = 'depressions_Polygons_Filtered'
downstreamNodePoints = "Downstream_Node_Points"

intermediate_data_list = [setNull_raster, streamOrder_raster, intRaster, rasterPoints_Depth, depressions_Polygon]

###########################
''' # 1 Create Vector OLFPs '''
###########################

if create_vector_OLFP:
    for threshold in stream_threshold_list:
        OLFP_Order_Polyline = 'OLFP_StreamOrder'
        OLFP_Order_Polyline = OLFP_Order_Polyline + '_{}k'.format(str(int(threshold)/1000.0).replace('.', '_'))

        # SET NULL RASTER
        printme('Creating Vector OLFPs...')
        printme('Executing Set Null Raster...')
        # Set local variables
        inRaster = Raster(flow_accumulation_raster)
        inFalseRaster = 1
        whereClause = "VALUE <= {}".format(threshold)
        # Execute SetNull
        outSetNull = SetNull(inRaster, inFalseRaster, whereClause)
        # Save the output
        outSetNull.save(setNull_raster)

        # STREAM ORDER RASTER
        printme('Calculating stream order...')
        # Set local variables
        inStreamRast = setNull_raster
        inFlowDirectionRaster = flow_direction_raster
        orderMethod = "STRAHLER"
        # Execute StreamOrder
        outStreamOrder = StreamOrder(inStreamRast, inFlowDirectionRaster, orderMethod)
        # Save the output 
        outStreamOrder.save(streamOrder_raster)

        # STREAM TO FEATURE
        printme('Creating Stream Features...')
        # Set local variables
        inStreamRaster = streamOrder_raster
        inFlowDir = flow_direction_raster
        outStreamFeats = OLFP_Order_Polyline
        # Execute 
        StreamToFeature(inStreamRaster, inFlowDir, outStreamFeats, "NO_SIMPLIFY")
        arcpy.management.AddFields(outStreamFeats, "StreamOrder DOUBLE # # # #")
        arcpy.management.CalculateField(outStreamFeats, "StreamOrder", "int(!grid_code!)", "PYTHON3", '')

        #  # UPDATE STREAM WITH CATCHMENT AREA
        # printme ('Calculating Downstream  Node Catchment Size...')
        # arcpy.management.AddFields(outStreamFeats, "DS_Node_X DOUBLE # # # #;DS_Node_Y DOUBLE # # # #")
        # arcpy.management.CalculateGeometryAttributes(outStreamFeats, "DS_Node_X LINE_END_X;DS_Node_Y LINE_END_Y", '', '', None)
        # arcpy.management.XYTableToPoint(outStreamFeats, "in_memory\\DS_Node_Points", "DS_Node_X", "DS_Node_Y")
        # arcpy.management.XYTableToPoint(outStreamFeats, "in_memory\\DS_Node_Points", "DS_Node_X", "DS_Node_Y", "#", arcpy.SpatialReference(2193))
        # arcpy.sa.ExtractMultiValuesToPoints("in_memory\\DS_Node_Points", [[flow_accumulation_raster.strip("'"), "Catchment_Area_Ha"]], "NONE")
        # arcpy.management.CalculateField("in_memory\\DS_Node_Points", "Catchment_Area_Ha", "(!Catchment_Area_Ha!*4)/10000", "PYTHON3", '')
        # arcpy.management.JoinField(outStreamFeats, "arcid", "in_memory\\DS_Node_Points", "arcid", "Catchment_Area_Ha")
        # arcpy.CopyFeatures_management("in_memory\\DS_Node_Points", downstreamNodePoints)

        # UPDATE STREAM WITH CATCHMENT AREA
        printme('Calculating Downstream  Node Catchment Size'
                '...')
        arcpy.management.AddGeometryAttributes(outStreamFeats, "LINE_START_MID_END", "METERS", '', arcpy.SpatialReference(2193))
        arcpy.management.XYTableToPoint(outStreamFeats, "in_memory\\DS_Node_Points", "MID_X", "MID_Y", "#", arcpy.SpatialReference(2193))
        arcpy.sa.ExtractMultiValuesToPoints("in_memory\\DS_Node_Points", [[flow_accumulation_raster.strip("'"), "Catchment_Area_Ha"]], "NONE")
        arcpy.management.CalculateField("in_memory\\DS_Node_Points", "Catchment_Area_Ha", "(!Catchment_Area_Ha!*4)/10000", "PYTHON3", '')
        arcpy.management.JoinField(outStreamFeats, "arcid", "in_memory\\DS_Node_Points", "arcid", "Catchment_Area_Ha")
        arcpy.CopyFeatures_management("in_memory\\DS_Node_Points", downstreamNodePoints)
        arcpy.management.DeleteField("OLFP_StreamOrder_0_5k", "arcid;END_X;END_Y;from_node;grid_code;MID_X;MID_Y;START_X;START_Y;to_node")


if create_depressions:

    # SET NULL RASTER
    printme('Creating depression layer...')
    printme('Executing Set Null Raster...')

    # Set local variables
    inRaster = Raster(depression_raster)
    inFalseRaster = 1
    whereClause = "VALUE <= {}".format(depression_threshold)
    # Execute SetNull
    outSetNull = SetNull(inRaster, inFalseRaster, whereClause)
    # Save the output 
    outSetNull.save(setNull_raster)

    # # # INT RASTER
    # # printme('Converting to Int Raster...')
    # # # Set local variables
    # # inRaster = setNull_raster
    # # # Execute Int
    # # outInt = Int(inRaster)
    # # # Save the output 
    # # outInt.save(intRaster)

    # CREATE RASTER POINTS
    printme('Create Raster Points...')
    # Set local variables
    inRaster = setNull_raster
    outPoint = rasterPoints
    field = "VALUE"
    # Execute RasterToPoint
    arcpy.RasterToPoint_conversion(inRaster, outPoint, field)

    # CONVERT RASTER TO POLYGONS
    printme('Creating Polygon Footprints...')
    # Set local variables
    inRaster = setNull_raster
    outPolygons = depressions_Polygon
    field = "VALUE"
    # Execute RasterToPolygon
    arcpy.RasterToPolygon_conversion(inRaster, outPolygons, "SIMPLIFY", field)

    # EXTRACT DEPRESSION VALUES
    printme('Selecting relevant Points...')
    # CREATE FEATURE LAYERS
    # Make a layer from the feature class
    arcpy.MakeFeatureLayer_management(outPolygons, 'depressionPolyLyr_100m')
    arcpy.MakeFeatureLayer_management(rasterPoints, 'rasterPointsLyr')
    arcpy.SelectLayerByAttribute_management('depressionPolyLyr_100m', "NEW_SELECTION", "Shape_Area >= 100")
    arcpy.SelectLayerByLocation_management("rasterPointsLyr", "INTERSECT", "depressionPolyLyr_100m", "", "NEW_SELECTION")

    # EXTRACT DEPRESSION VALUES FROM RASTER
    printme('Extracting Depression cell Values...')
    # Set local variables
    inPointFeatures = "rasterPointsLyr"
    inRaster = depression_raster
    outPointFeatures = rasterPoints_Depth
    # Execute ExtractValuesToPoints
    ExtractValuesToPoints(inPointFeatures, inRaster, outPointFeatures, "INTERPOLATE", "VALUE_ONLY")

    # CALCULATE CELL VOLUME
    printme('Calculate 3D surface area...')
    cellsize = 2
    cellsize = cellsize**cellsize   
    arcpy.AddField_management(outPointFeatures, 'SurfaceVol', "DOUBLE")
    arcpy.CalculateField_management(outPointFeatures, "SurfaceVol", '!RASTERVALU! * {}'.format(str(cellsize)), "PYTHON3")

    # UPDATE POLYGON DEPRESSION TABLE
    printme('Create final intersect...')
    arcpy.analysis.SpatialJoin('depressionPolyLyr_100m', rasterPoints_Depth, depressions_Polygons_Filtered, "JOIN_ONE_TO_ONE", "KEEP_ALL", 'Shape_Length "Shape_Length" false true true 8 Double 0 0,First,#,Depressions_Poly,Shape_Length,-1,-1;Shape_Area "Shape_Area" false true true 8 Double 0 0,First,#,Depressions_Poly,Shape_Area,-1,-1;MIN "MIN" true true false 4 Double 0 0,Min,#,rasterPoints_Depth,RASTERVALU,-1,-1;MAX "MAX" true true false 255 Double 0 0,Max,#,rasterPoints_Depth,RASTERVALU,-1,-1;SurfaceVol "SurfaceVol" true true false 8 Double 0 0,Sum,#,rasterPoints_Depth,SurfaceVol,-1,-1', "INTERSECT", None, None) 
    printme('Depression Polygons Complete...')


for data_lyr in intermediate_data_list:
    try:
        arcpy.Delete_management(data_lyr)
    except:
        print('{} could not be deleted'.format(data_lyr))
