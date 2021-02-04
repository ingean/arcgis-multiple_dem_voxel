import os
import arcpy

def create_featureclass(fc, template_fc):
  fc_path = os.path.split(fc)
  delete_fc(fc) # Delete if already exist

  print("Creating feature class {}...".format(fc_path[1]))
  spatial_ref = arcpy.Describe(template_fc).spatialReference

  return arcpy.CreateFeatureclass_management(fc_path[0], fc_path[1], "POINT", template_fc, 
                                    "DISABLED", "ENABLED", spatial_ref)

def delete_fc(fc_path):
  if arcpy.Exists(fc_path):
    print("Deleting feature class {} ".format(fc_path))
    arcpy.Delete_management(fc_path)