import logging
import arcpy
from modules.data_mgmt import create_featureclass

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger(__name__)

def fishnet_2_point_cube(cube_path, fishnet_fc, ext, res):
  z_layers = (ext['max_z'] - ext['min_z']) / abs(res['z'])
  log.info(f"Creating cube {cube_path}...")
  log.info(f"Adding {z_layers} layers of points")
  
  cube_fc = create_featureclass(cube_path, fishnet_fc)
  arcpy.management.AddField(cube_fc, 'X', 'DOUBLE')
  arcpy.management.AddField(cube_fc, 'Y', 'DOUBLE')
  arcpy.management.AddField(cube_fc, 'Z', 'FLOAT')
  z = ext['min_z']

  while z <= ext['max_z']:
    copy_points(fishnet_fc, cube_fc, z, None)
    z += abs(res['z'])

  log.info("Finished creating 3D point cube from fishnet!")


def copy_points(input_fc, output_fc, z, time):
  log.info(f"Copying points for height: {z}...")

  fields = arcpy.Describe(output_fc).fields
  field_names = [field.name if field.name != 'Shape' else 'SHAPE@' for field in fields]
  
  output =  arcpy.da.InsertCursor(output_fc,field_names)
  
  with arcpy.da.SearchCursor(input_fc,"*") as cursor:
    for r in cursor:
      f = list(r[2:]) # Copy all attributes except object id and shape

      f.insert(0, (r[1][0],r[1][1], z)) # Add 3D-point shape
      f.insert(0, r[0]) # Add object id

      #f.append(r[1][0]) # Add x-coordinate to attributes
      #f.append(r[1][1]) # Add y-coordinate to attributes
      f.append(z) # Add z-coordinate to attributes

      output.insertRow(tuple(f))
      
  del output