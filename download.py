import requests
import matplotlib.pyplot as plt
from rasterio.plot import show
import urllib
import rasterio
import rasterio.windows as win
from rasterio.crs import CRS
from rasterio.warp import transform_bounds
import os

# Search
def search():
  stac_endpoint = "https://earth-search.aws.element84.com/v0/search"
  dt = "2022-01-01T00:00:00Z" + "/" + "2022-03-01T00:00:00Z"
  bbox = [160.6,-55.95,-170,-25.89]
  bbox = [-110,39.5,-105,40.5]
  bbox_pt = [-7.6551,40.0529,-7.3585,40.1889]
  cloud_cover = 20

  query = {
      "collections": ["sentinel-s2-l2a-cogs"], # Make sure to query only sentinel-2 COGs collection
      "datetime": dt,
      "limit": 10, # max limit is 10000, default is 10
      "query": {
          "eo:cloud_cover": {
              "lt": cloud_cover
          }  # Use low cloud cover
      },
      "bbox": bbox_pt,
      #"intersects": geom,
      "fields": {
        'include': ['id', 'properties.datetime', 'properties.eo:cloud_cover'],  # Make returned response ligth 
        'exclude': ['links']
      }
  }

  headers = {
      "Content-Type": "application/json",
      "Accept-Encoding": "gzip",
      "Accept": "application/geo+json",
  }


  search = requests.post(stac_endpoint, headers=headers, json=query).json()
  if search and len(search['features']) > 0:
      dates = [f["properties"]["datetime"][0:10] for f in search["features"]]
      thumbs = [f["assets"]["thumbnail"]["href"] for f in search["features"]]
  print(search['numberReturned'], "items found")
  print("dates:", dates)


def download(bbox):
  bbox_crs = CRS.from_epsg("4326")
  # buffer in meters
  buffer = 0

  with rasterio.open("B02.tif") as src:
      # bounds (left, bottom, right, top)
      bounds = transform_bounds(bbox_crs,src.crs, bbox)
      if buffer > 0:
          bounds = (bounds[0]-buffer, bounds[1]-buffer, bounds[2]+buffer, bounds[3]+buffer)
      w = win.from_bounds(*bounds, src.transform)
      b1 = src.read(1, window=w)
      
  with rasterio.open("B03.tif") as src2:
      bounds = transform_bounds(bbox_crs,src2.crs, *bbox)
      if buffer > 0:
          bounds = (bounds[0]-buffer, bounds[1]-buffer, bounds[2]+buffer, bounds[3]+buffer)
      w = win.from_bounds(*bounds, src2.transform)
      b2 = src2.read(1, window=w)
      out_meta = src2.meta
      out_transform = src2.transform
      out_nodata = src2.nodata
    
def save(out_image, out_meta, out_transform, nodata, dir, filename, delete):
  if dir:
    os.makedirs(dir, exist_ok=True)
    filename = dir + "/" + filename
  kwargs = out_meta
  kwargs.update({'driver': 'GTiff', 'height': out_image.shape[0],
                    'width': out_image.shape[1], 'transform': out_transform,
                    'nodata': nodata, 'dtype': rasterio.float32})
  with rasterio.open(filename, 'w', **kwargs) as dst:
      dst.write_band(1, out_image.astype(rasterio.float32))
  #send_to_minio(dir+filename, filename.replace("_", "/"))
  if delete:
      os.remove(dir+filename)

if __name__ == '__main__':
  res = search()
  for 
    img = download()
    save(im)
