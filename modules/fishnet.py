import logging
import arcpy
from arcpy.sa import *
from modules.data_mgmt import delete_fc, calculate_geometry

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger(__name__)

def create_fishnet(out_fc, temp_extent, res):

  delete_fc(out_fc) # Delete existing fishnet polygons
  delete_fc(out_fc + "_label") # Delete existing fishnet label points
  
  log.info(f"Creating {res['x']} x {res['y']} fishnet for {temp_extent}...")
  arcpy.env.outputZFlag = "Enabled"
  d = arcpy.Describe(temp_extent)
 
  arcpy.CreateFishnet_management(
    out_fc, 
    f'{d.extent.XMin} {d.extent.YMin}',
    f'{d.extent.XMin} {d.extent.YMax}', 
    res['x'],
    res['y'], 
    '#', '#', '#', 
    'LABELS', 
    d.extent, 
    'POLYGON')

  calculate_geometry(f"{out_fc}_label")
  log.info("Finished creating fishnet!")

def tag_fishnet(fishnet_fc, a_extent):
  log.info(f"Tagging points in {fishnet_fc} fishnet for analysis extent {a_extent}...")
  arcpy.management.AddField(fishnet_fc, 'AOI', 'SHORT')
  fishnet_layer = arcpy.management.MakeFeatureLayer(fishnet_fc, 'fishnet_layer')

  log.info("Selecting all fishnet points within analysis extent...")
  fishnet_sel = arcpy.management.SelectLayerByLocation(
    fishnet_layer,
    'WITHIN',
    a_extent)

  log.info("Calculating AOI value for selected features...")
  arcpy.management.CalculateField(
    fishnet_sel,
    'AOI',
    '1')

  log.info("Calculating AOI value for features outside selection...")
  codeblock = """def setAOI(aoi):
      if aoi == 1:
          return 1
      else:
          return 0"""

  arcpy.management.CalculateField(fishnet_fc,'AOI',
                                  'setAOI(!AOI!)','PYTHON3', codeblock)

  log.info("Finished tagging fishnet!")

def add_dem_heights(fishnet_fc, dem_folder, in_rasters):
  log.info(f"Adding heights to {fishnet_fc} fishnet for DEMs in folder {dem_folder}...")
  
  arcpy.env.workspace = dem_folder
  ExtractMultiValuesToPoints(fishnet_fc, in_rasters)

  log.info("Finished adding heights to fishnet!")
