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
  z_dim = ((round(desc.extent.ZMax, 1) - round(desc.extent.ZMin, 1)) / res['z']) + 1

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
    round(desc.extent.ZMin, 4), 
    round(desc.extent.ZMax, 4) + res['z'], res['z']).tolist()

  print("Finished assigning coordinate variables!")
  return ds

def assign_values(input_fc, ds, it):
  print("Adding data for timestep {}...".format(it))
  sql = 'ORDER BY X, Y, Z'

  with arcpy.da.SearchCursor(input_fc, "*", sql_clause=(None, sql)) as cursor:
    
    first = True
    ix, iy, iz, i, prev_x, prev_y = 0, 0, 0, 0, 0, 0
    
    for r in cursor:
      x = coord('X', r, cursor)
      y = coord('Y', r, cursor)
      z = coord('Z', r, cursor)
      
      if first:
        first = False
        prev_x = x
        prev_y = y
      else:
        if prev_x != x:
          ix += 1
          iy = 0
          iz = 0
          prev_x = x
          prev_y = y
        elif prev_y != y:
          iy += 1
          iz = 0
          prev_y = y
          
      ds['value'][it,iz,iy,ix] = calc_value(r, it)

      iz += 1
      i += 1

  print("Finished adding data for timestep!")
  return ds

def coord(field_name, row, cursor):
  return round(row[cursor.fields.index(field_name)], 4)

def calc_value(row, i):
  v = 1
  aoi = row[2]
  org_height = row[3] # Terrain height before building
  height = row[i + 4] # Terrain height at current time
  z = row[18] # Current voxel point height

  if height is None or aoi == 0: 
    height = org_height

  if z > org_height and z <= height: # Deposit
    v = 3
  elif z < org_height and z >= height: # Excavation
    v = 2
  elif z > height:
    v = 0
    
  return v

def point_cube_2_netcdf(point_fc, nc_path, ext, res):
  
  # Calculate the x, y, z, t dimensions of the NetCDF dataset to create
  calc_dim(point_fc, ext, res)

  # Create NetCDF dataset with dimensions and variables
  ds = create_netcdf_ds(nc_path)

  # Assign coordinate variables
  ds = assign_coord_values(point_fc, ds, ext, res)

  # Assign variables for each timestep
  i = 0
  while i < t_dim: # Repeat for each timestep 
    ds = assign_values(point_fc, ds, i)
    i += 1

  ds.close()
  print("Finished converting points to NetCDF!")


