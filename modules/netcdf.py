import os
import datetime
import arcpy
import netCDF4 as nc
import numpy as np

x_dim = 51
y_dim = 25
z_dim = 51
t_dim = 12

def calc_dim(cube_fc, ext, res):
  print("Calculating dimensions for: {}...".format(cube_fc))
  desc = arcpy.Describe(cube_fc)
  global x_dim
  x_dim = ((round(desc.extent.XMax, 4) - round(desc.extent.XMin, 4)) / res['x']) + 1

  global y_dim
  y_dim = ((round(desc.extent.YMax, 4) - round(desc.extent.YMin, 4)) / res['y']) + 1

  global z_dim
  z_dim = ((ext['max_z'] - ext['min_z']) / res['z']) + 1

  global t_dim
  t_dim = ((ext['max_t'] - ext['min_t']).days / res['t'])

  print("X-dimensions: {}".format(x_dim))
  print("Y-dimensions: {}".format(y_dim))
  print("Z-dimensions: {}".format(z_dim))
  print("T-dimensions: {}".format(t_dim))

def create_netcdf_ds(output_file):
  print("Creating NetCDF dataset: {}...".format(output_file))
  ds = nc.Dataset(output_file, 'w', format='NETCDF4')
  
  # Dimensions
  print("Creating dimensions...")
  
  time = ds.createDimension('time', None)
  x = ds.createDimension('x', x_dim)
  y = ds.createDimension('y', y_dim)
  z = ds.createDimension('z', z_dim)

  # Coordinate variables
  print("Creating coordinate variables...")
  
  calendar = 'standard'
  units = 'days since 1990-01-01 00:00'
  times = ds.createVariable('time', 'f4', ('time',))
  times.units = units
  x_coords = ds.createVariable('x', 'f8', ('x',))
  x_coords.units = 'Meter'
  y_coords = ds.createVariable('y', 'f8', ('y',))
  y_coords.units = 'Meter'
  z_coords = ds.createVariable('z', 'f4', ('z',))
  z_coords.units = 'Meter'
  
  # Variables
  print("Creating variables...")
  
  value = ds.createVariable('value', 'u1', ('time','z', 'y', 'x' )) # ArcGIS Expects time,z,y,x dimension order
  value.units = 'Unsigned integer'

  print("Finished creating NetCDF dataset")
  return ds

def assign_coord_values(input_fc, ds, ext, res): 
  
  print("Assigning values to coordinate variables...")
  desc = arcpy.Describe(input_fc)
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
    ext['max_z'] + res['z'], res['z']).tolist()

  print("Finished assigning coordinate variables!")
  return ds

def assign_values(input_fc, ds, ext, res, it):
  print("Adding data for timestep {}...".format(it))
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
      
      for iz in range(int(z_dim)):
        if prev_x != x:
          ix += 1
          iy = 0
          prev_x = x
          prev_y = y
        elif prev_y != y:
          iy += 1
          prev_y = y
            
        ds['value'][it,iz,iy,ix] = calc_value(r, z, it)
        z += res['z']

  print("Finished adding data for timestep!")
  return ds

def coord(field_name, row, cursor):
  return round(row[cursor.fields.index(field_name)], 4)

def calc_value(row, z, i):
  v = 1
  aoi = row[4]
  org_height = row[5] # Terrain height before building
  tin_height = row[18] # Planned terrain height
  height = row[i + 6] # Terrain height at current time

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

def point_cube_2_netcdf(point_fc, nc_path, ext, res):
  print("Starting to convert fishnet to NetCDF...")
  print("Operation started at: {}".format(datetime.datetime.now()))
  # Calculate the x, y, z, t dimensions of the NetCDF dataset to create
  calc_dim(point_fc, ext, res)

  # Create NetCDF dataset with dimensions and variables
  ds = create_netcdf_ds(nc_path)

  # Assign coordinate variables
  ds = assign_coord_values(point_fc, ds, ext, res)

  # Assign variables for each timestep
  for i in range(int(t_dim)): # Repeat for each timestep 
    ds = assign_values(point_fc, ds, ext, res, i)
  
  ds.close()
  print("Finished converting points to NetCDF!")
  print("Operation ended at: {}".format(datetime.datetime.now()))


