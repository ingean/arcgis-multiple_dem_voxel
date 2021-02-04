###############################################################################
## Creates a NetCDF file with changes between multiple overlapping DEMs      ##
##                                                                           ## 
##  1. Creates a point fishnet for an bounding box (polygon)                 ##
##  2. Marks all points within analysis extent with AOI = 1                  ##
##  3. Extracts heights from a catalog of DEMs                               ##
##     and adds as attributes to points                                      ##
##  4. Creates a 3D point cube from point fishnet, copying all attributes    ##
##  5. Converts 3D point cube to a z,y,x,time NetCDF with values describing  ##
##     if voxel / point is over or under ground or has been changed          ##
##     since first DEM (point height is between original and new DEM).       ##
##  6. Interpolates height values between DEM capture dates                  ## 
###############################################################################

import os
import datetime
from modules.fishnet import create_fishnet, tag_fishnet, add_dem_heights
from modules.point_cube import fishnet_2_point_cube
from modules.netcdf import point_cube_2_netcdf 

###############################################################################
## Parameters
###############################################################################

# Workspace
gdb = r"D:\Data\GeoTek_21\Voxel\Voxel.gdb"
folder = r"D:\Data\GeoTek_21\Voxel"

# Area of interest
bbox_fc = os.path.join(gdb, r"Voxel_bounding_box")
extent_fc = os.path.join(gdb, r"Voxel_analysis_extent")

ext = { # Height and time extents
  "max_z": 210, #m.a.s.l
  "min_z": 160, #m.a.s.l
  "min_t": datetime.datetime(2020, 6, 11),
  "max_t": datetime.datetime(2020, 6, 23)
}

res = { # Analysis resolution
  "x": 10, #meters
  "y": 10, #meters
  "z": 1, #meters
  "t": 1 #days
}

# Input data
dem_folder = r"D:\Data\GeoTek_21\Skanska\Kleggerud_Alle_DEM"
dems = [["terrain.tif","Height"],
        ["Kleggerud_Svartskifer_200611-DEM.tiff","Height_11_06_2020"], 
        ["Kleggerud_Svartskifer_200616-DEM.tiff","Height_16_06_2020"], 
        ["Kleggerud_Svartskifer_200618-DEM.tiff","Height_18_06_2020"], 
        ["Kleggerud_Svartskifer_200620-DEM.tiff","Height_20_06_2020"], 
        ["Kleggerud_Svartskifer_200625-DEM.tiff","Height_25_06_2020"], 
        ["Kleggerud_Svartskifer_200626-DEM.tiff","Height_26_06_2020"], 
        ["Kleggerud_Svartskifer_200627-DEM.tiff","Height_27_06_2020"], 
        ["Kleggerud_Svartskifer_200630-DEM.tiff","Height_30_06_2020"], 
        ["Kleggerud_Svartskifer_200725-DEM.tiff","Height_25_07_2020"], 
        ["Kleggerud_Svartskifer_200825-DEM.tiff","Height_25_08_2020"], 
        ["Kleggerud_Svartskifer_200905-DEM.tiff","Height_05_09_2020"],
        ["Kleggerud_Svartskifer_200908-DEM.tiff","Height_08_09_2020"]]

# Output data
fishnet_poly_fc = os.path.join(gdb, r"points_fishnet")
fishnet_fc = os.path.join(gdb, r"points_fishnet_label")
points_cube_fc = os.path.join(gdb, r"points_cube")
nc_results_file = os.path.join(folder, r"nc_time_result.nc")

###############################################################################
## Script
###############################################################################

# Create fishnet for analysis bounding box
#create_fishnet(fishnet_poly_fc, bbox_fc, res)

# Tag points in fishnet with analysis extent
#tag_fishnet(fishnet_fc, extent_fc)

# Add DEM heights as attributes to fishnet points
#add_dem_heights(fishnet_fc, dem_folder, dems)

# Add z-dimension to fishnet to create 3D point cube
#fishnet_2_point_cube(points_cube_fc, fishnet_fc, ext, res)

# Convert 3D point cube to NetCDF-file
point_cube_2_netcdf(points_cube_fc, nc_results_file, ext, res)
