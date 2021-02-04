import arcpy
from arcpy.sa import *

def create_fishnet(out_fc, temp_extent, res):
  
  arcpy.env.outputZFlag = "Enabled"
  
  print("Creating {} x {} fishnet for {}...".format(res['x'], res['y'], temp_extent))
  
  desc = arcpy.Describe(temp_extent)
  x_min = desc.extent.XMin
  y_min = desc.extent.YMin
  y_max = desc.extent.YMax

  arcpy.CreateFishnet_management(
    out_fc, 
    '{} {}'.format(x_min, y_min),
    '{} {}'.format(x_min, y_max),
    res['x'],
    res['y'], 
    '#', '#', '#', 
    'LABELS', 
    desc.extent, 
    'POLYGON')

  print("Finished creating fishnet!")


def tag_fishnet(fishnet_fc, a_extent):
  print("Tagging points in {} fishnet for analysis extent {}...".format(fishnet_fc, a_extent))
  print("Adding field AOI...")

  arcpy.management.AddField(
    fishnet_fc, 
    'AOI', 
    'SHORT')

  print("Finished adding field.")
  print("Creating a feature layer from fishnet feature class...")
  fishnet_layer = arcpy.management.MakeFeatureLayer(fishnet_fc, 'fishnet_layer')

  print("Finished creating feature layer")
  print("Selecting all fishnet points within analysis extent...")
  fishnet_sel = arcpy.management.SelectLayerByLocation(
    fishnet_layer,
    'WITHIN',
    a_extent)

  print("Finished selecting features in analysis extent.")
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

  arcpy.management.CalculateField(
    fishnet_fc,
    'AOI',
    'setAOI(!AOI!)',
    'PYTHON3', 
    codeblock)

  print("Finished tagging fishnet!")

def add_dem_heights(fishnet_fc, dem_folder, in_rasters):
  print("Adding heights to {} fishnet for DEMs in folder {}...".format(fishnet_fc, dem_folder))
  
  arcpy.env.workspace = dem_folder
  ExtractMultiValuesToPoints(fishnet_fc, in_rasters)

  print("Finished adding heights to fishnet!")