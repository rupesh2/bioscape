#!/usr/bin/env python3
"""Create bounding geojson for AVIRIS V2 RFL NetCDF4 tiles"""

from os import path
import xarray as xr
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
import s3fs

s3 = s3fs.S3FileSystem(anon=False)
data = []

# loop AVNG_V2
for fid in s3.ls('bioscape-data/AVNG_V2/'):
    # exclude other e.g., flight line folder
    if path.basename(fid).startswith('ang'):
        # loop through all tile files
        for f1 in s3.ls(fid):
            # only select reflectance files
            rf= [g for g in s3.ls(f1) if g.endswith('RFL_ORT.nc')]
            # if reflectance file exists
            if rf:
                r = f's3://{rf[0]}'
                # open reflectance file
                ds = xr.open_dataset(s3.open(r, mode='rb'),
                                     engine="h5netcdf")
                # create bounding box using min,max coordinates
                bound = box(ds.easting.min().data, ds.northing.min().data,
                          ds.easting.max().data, ds.northing.max().data)
                # append s3 path and bounds
                data.append([path.basename(fid),
                             path.splitext(r)[0]+'.nc',
                             ds.attrs['time_coverage_end'],
                             bound])
            else:
                # print if RFL file does not exist
                print(s3.ls(f1))
# pandas dataframe
df =pd.DataFrame(data, columns=['fid','RFL s3','end_time','geometry'])
# create geopandas dataframe, crs is UTM
gdf = gpd.GeoDataFrame(df, geometry=df.geometry, crs='32734')
# # reproject to WGS84 and export as geojson
gdf.to_crs('4326')[['fid','RFL s3','end_time','geometry']].to_file('ANGv2_Coverage.geojson',
                                                        driver="GeoJSON")

