import logging
import arcpy
import netCDF4 as nc
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger(__name__)

def calc_dim(cube_fc, ext, res):
  dims = {}


  log.info(f"Calculating dimensions for: {cube_fc}...")
  desc = arcpy.Describe(cube_fc)
 
  dims['x'] = ((round(desc.extent.XMax, 4) - round(desc.extent.XMin, 4)) / res['x']) + 1
  log.info(f"X-dimensions: {dims['x']}")

  dims['y'] = ((round(desc.extent.YMax, 4) - round(desc.extent.YMin, 4)) / res['y']) + 1
  log.info(f"Y-dimensions: {dims['y']}")

  dims['z'] = ((ext['max_z'] - ext['min_z']) / abs(res['z'])) + 1
  log.info(f"Z-dimensions: {dims['z']}")

  if 'max_t' in ext and 'min_t' in ext:
    dims['t'] = ((ext['max_t'] - ext['min_t']).days / res['t'])
    log.info(f"T-dimensions: {dims['t']}")
  
  return dims

def create_netcdf_ds(output_file, dims):
  log.info(f"Creating NetCDF dataset: {output_file}...")
  ds = nc.Dataset(output_file, 'w', format='NETCDF4')
  
  # Dimensions
  log.info("Creating dimensions...")
  if 't' in dims:
    time = ds.createDimension('time', None)
  x = ds.createDimension('x', dims['x'])
  y = ds.createDimension('y', dims['y'])
  z = ds.createDimension('z', abs(dims['z']))

  # Coordinate variables
  log.info("Creating coordinate variables...")
  
  if 't' in dims:
    times = ds.createVariable('time', 'f4', ('time',))
    times.units = 'days since 1990-01-01 00:00'
  
  x_coords = ds.createVariable('x', 'f8', ('x',))
  x_coords.units = 'Meter'
  y_coords = ds.createVariable('y', 'f8', ('y',))
  y_coords.units = 'Meter'
  z_coords = ds.createVariable('z', 'f4', ('z',))
  z_coords.units = 'Meter'
  
  # Variables
  log.info("Creating variables...")
  
  if 't' in dims:
    value = ds.createVariable('value', 'i1', ('time','z', 'y', 'x' )) # ArcGIS Expects time,z,y,x dimension order
  else:
    value = ds.createVariable('value', 'i1', ('z', 'y', 'x' )) # ArcGIS Expects time,z,y,x dimension order
  
  value.units = 'Unsigned integer'
  log.info("Finished creating NetCDF dataset")
  return ds

def assign_coord_values(input_fc, ds, ext, res): 
  
  log.info("Assigning values to coordinate variables...")
  desc = arcpy.Describe(input_fc)

  if 't' in res:
    ds['time'][:] = np.arange(
      nc.date2num(ext['min_t'], 'days since 1990-01-01 00:00', 'standard'), 
      nc.date2num(ext['max_t'], 'days since 1990-01-01 00:00', 'standard') + res['t'], res['t']).tolist()

  ds['x'][:] = np.arange(
    round(desc.extent.XMin, 4), 
    round(desc.extent.XMax, 4) + res['x'], res['x']).tolist()

  ds['y'][:] = np.arange(
    round(desc.extent.YMin, 4), 
    round(desc.extent.YMax, 4) + res['y'], res['y']).tolist()

  ds['z'][:] = np.arange(
    ext['min_z'], 
    ext['max_z'] + abs(res['z']), abs(res['z'])).tolist()

  log.info("Finished assigning coordinate variables!")
  return ds

def assign_values(input_fc, ds, ext, res, dims, it = None):
  if 't' in res:
    log.info(f"Adding data for timestep {it}...")
  else:
    log.info("Adding data...")
  
  sql = 'ORDER BY X, Y'

  with arcpy.da.SearchCursor(input_fc, "*", sql_clause=(None, sql)) as cursor:
    ix, iy, prev_x, prev_y, first = 0, 0, 0, 0, True
    
    for r in cursor:
      
      if first:
        prev_x = coord('X', r, cursor)
        prev_y = coord('Y', r, cursor)
        first = False
      
      x = coord('X', r, cursor)
      y = coord('Y', r, cursor)
      z = ext['min_z']
      
      for iz in range(int(dims['z'])):
        if prev_x != x:
          ix += 1
          iy = 0
          prev_x = x
          prev_y = y
        elif prev_y != y:
          iy += 1
          prev_y = y
        if 't' in res:    
          ds['value'][it,iz,iy,ix] = calc_value_time(r, z, it)
        else:
          ds['value'][iz,iy,ix] = calc_value(r, z)

        z += abs(res['z'])

  log.info("Finished adding data.")
  return ds

def coord(field_name, row, cursor):
  return round(row[cursor.fields.index(field_name)], 4)

def calc_value_time(row, z, i):
  v = 1
  aoi = row[4]
  org_height = row[5] # Terrain height before building
  tin_height = row[18] # Planned terrain height
  height = org_height # Use terrain before building for first timestep
  
  if i != 0:
    #height = row[i + 6] # Terrain height at current time
    height = row[i + 5] # Terrain height from drone

  if tin_height is None:
    tin_height = org_height

  if height is None or aoi == 0: 
    height = org_height

  # Mark points in zone between planned and orginal heights
  if z > org_height and z < tin_height: # Planned deposit
    v = 5
  elif z > tin_height and z <= org_height: # Planned excavation
    v = 4

  # Mark points in zone between original and current heights
  if z > org_height and z <= height: # Deposit
    v = 3
  elif z < org_height and z >= height: # Excavation
    v = 2
  elif z > height:
    v = 0
    
  return v

def calc_value(row, z):
  r = -1
  aoi = row[4]
  if aoi == 0: return -1

  heights = list(row[5:])
  heights.insert(0, 0) # Add sea level

  for i,v in enumerate(heights):
      if i + 1 < len(heights):
          r = check(z, v, heights[i + 1], i)
      else:
          r = checkSingle(z, v, i)
      
      if r != -1: return r
  return r

def check(z,v1,v2,i):
  if v1 is None or v2 is None: return -1
  if z <= v1 and z > v2: 
    return i
  else:
    return -1
    
def checkSingle(z,v,i):
  if v is None: return -1
  if z <= v: 
    return i
  else: 
    return -1

def points_to_netcdf(point_fc, nc_path, ext, res):
  log.info("Starting to convert fishnet to NetCDF...")
  # Calculate the x, y, z, t dimensions of the NetCDF dataset to create
  dims = calc_dim(point_fc, ext, res)

  # Create NetCDF dataset with dimensions and variables
  ds = create_netcdf_ds(nc_path, dims)

  # Assign coordinate variables
  ds = assign_coord_values(point_fc, ds, ext, res)

  # Assign variables for each timestep
  if 't' in dims:
    for i in range(int(dims['t'])): # Repeat for each timestep 
      ds = assign_values(point_fc, ds, ext, res, dims, i)
  else:
    ds = assign_values(point_fc, ds, ext, res, dims)
  
  ds.close()
  log.info("Finished converting points to NetCDF!")



