import logging
import os
import re
import arcpy

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger(__name__)

def create_featureclass(fc, template_fc):
  
  fc_path = os.path.split(fc)
  delete_fc(fc) # Delete if already exist

  log.info(f"Creating feature class {fc_path[1]}...")
  spatial_ref = arcpy.Describe(template_fc).spatialReference

  return arcpy.CreateFeatureclass_management(fc_path[0], fc_path[1], "POINT", template_fc, 
                                    "DISABLED", "ENABLED", spatial_ref)

def delete_fc(fc_path):
  if arcpy.Exists(fc_path):
    log.info(f"Deleting feature class {fc_path}")
    arcpy.Delete_management(fc_path)

def calculate_geometry(fc):
  log.info("Adding X and Y coordinates to attribute table...")
  arcpy.management.AddField(fc, 'X', 'DOUBLE')
  arcpy.management.AddField(fc, 'Y', 'DOUBLE')
  arcpy.CalculateGeometryAttributes_management(
    fc, [["X", "POINT_X"], ["Y", "POINT_Y"]])
  
  log.info("Finished calculating geometry!")


def suffix(res):
  x = "".join([c for c in str(res['x']) if re.match(r'\w', c)])
  y = "".join([c for c in str(res['y']) if re.match(r'\w', c)])
  z = "".join([c for c in str(res['z']) if re.match(r'\w', c)])

  return f"_{x}x{y}x{z}"