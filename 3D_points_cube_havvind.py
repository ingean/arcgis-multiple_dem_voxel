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

import logging
import os
import datetime
from modules.data_mgmt import suffix
from modules.fishnet import create_fishnet, tag_fishnet, add_dem_heights
from modules.point_cube import fishnet_2_point_cube 

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger(__name__)

###############################################################################
## Parameters
###############################################################################

# Workspace
GDB = r"D:\Data\GeoTek_22\Havvind_voxler\point_cubes.gdb"
PROJECT_FOLDER = r"D:\Data\GeoTek_22\Havvind_voxler"

# Area of interest
BBOX_FC = os.path.join(GDB, r"analysis_extent_all")
EXTENT_FC = os.path.join(GDB, r"analysis_aoi_all")

NC_EXTENT = { # Height and time extents
  "max_z": 0, # m.a.s.l
  "min_z": -115, # m.a.s.l
}

NC_RESOLUTION = { # Analysis resolution
  "x": 100, # meters
  "y": 100, # meters
  "z": 1, # meters
}

# Input data
DEM_GDB = r"D:\Data\GeoTek_22\Havvind_voxler\Horizons.gdb"
DEMS = [["RVO_HKN_MBES_DEM_0_5m","Seabed"],
        ["RVO_HKN_Geological_Horizon_LAT_H01","H01"], # DEM file name, spot height field name
        ["RVO_HKN_Geological_Horizon_LAT_H05_","H05"], 
        ["RVO_HKN_Geological_Horizon_LAT_H10","H10"], 
        ["RVO_HKN_Geological_Horizon_LAT_H20","H20"]]

# Output data
FILE_SUFFIX = suffix(NC_RESOLUTION)
FISHNET_FC_POLY = os.path.join(GDB, f"fishnet_all{FILE_SUFFIX}")
FISHNET_FC = f"{FISHNET_FC_POLY}_label"
#fishnet_fc = os.path.join(gdb, r"fishnet_1x1x05_interpolate")
NC_FILE = os.path.join(PROJECT_FOLDER, f"voxel{FILE_SUFFIX}.nc")
POINT_CUBE = os.path.join(GDB, f"{FISHNET_FC}_3D_point_cube")

###############################################################################
## Script
###############################################################################

# Create fishnet for analysis bounding box
create_fishnet(FISHNET_FC_POLY, BBOX_FC, NC_RESOLUTION)

# Tag points in fishnet with analysis extent
tag_fishnet(FISHNET_FC, EXTENT_FC)

# Add DEM heights as attributes to fishnet points
add_dem_heights(FISHNET_FC, DEM_GDB, DEMS)

# Convert to 3D point cube
fishnet_2_point_cube(POINT_CUBE, FISHNET_FC, NC_EXTENT, NC_RESOLUTION)

log.info(f"Script ended!")
