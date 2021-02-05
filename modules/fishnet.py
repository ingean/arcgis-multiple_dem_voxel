import datetime
import arcpy
from arcpy.sa import *
from modules.data_mgmt import delete_fc, calculate_geometry

def create_fishnet(out_fc, temp_extent, res):

  delete_fc(out_fc) # Delete existing fishnet polygons
  delete_fc(out_fc + "_label") # Delete existing fishnet label points
  
  print("Creating {} x {} fishnet for {}...".format(res['x'], res['y'], temp_extent))
  arcpy.env.outputZFlag = "Enabled"
  d = arcpy.Describe(temp_extent)
 
  arcpy.CreateFishnet_management(
    out_fc, 
    '{} {}'.format(d.extent.XMin, d.extent.YMin),
    '{} {}'.format(d.extent.XMin, d.extent.YMax),
    res['x'],
    res['y'], 
    '#', '#', '#', 
    'LABELS', 
    d.extent, 
    'POLYGON')

  calculate_geometry(out_fc + "_label")
  print("Finished creating fishnet!")

def tag_fishnet(fishnet_fc, a_extent):
  print("Tagging points in {} fishnet for analysis extent {}...".format(fishnet_fc, a_extent))
  arcpy.management.AddField(fishnet_fc, 'AOI', 'SHORT')
  fishnet_layer = arcpy.management.MakeFeatureLayer(fishnet_fc, 'fishnet_layer')

  print("Selecting all fishnet points within analysis extent...")
  fishnet_sel = arcpy.management.SelectLayerByLocation(
    fishnet_layer,
    'WITHIN',
    a_extent)

  print("Calculating AOI value for selected features...")
  arcpy.management.CalculateField(
    fishnet_sel,
    'AOI',
    '1')

  print("Calculating AOI value for features outside selection...")
  codeblock = """def setAOI(aoi):
      if aoi == 1:
          return 1
      else:
          return 0"""

  arcpy.management.CalculateField(fishnet_fc,'AOI',
                                  'setAOI(!AOI!)','PYTHON3', codeblock)

  print("Finished tagging fishnet!")

def add_dem_heights(fishnet_fc, dem_folder, in_rasters):
  print("Adding heights to {} fishnet for DEMs in folder {}...".format(fishnet_fc, dem_folder))
  print("Operation started at: {}".format(datetime.datetime.now()))
  
  arcpy.env.workspace = dem_folder
  ExtractMultiValuesToPoints(fishnet_fc, in_rasters)

  print("Finished adding heights to fishnet!")
  print("Operation ended at: {}".format(datetime.datetime.now()))