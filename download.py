import requests
import urllib
import rasterio
import rasterio.windows as win
from rasterio.crs import CRS
from rasterio.warp import transform_bounds
from rasterio.enums import Resampling
import os

# Search
def search(bbox, datetime, cloudcover=20, limit=20):
  stac_endpoint = "https://earth-search.aws.element84.com/v0/search"

  query = {
      "collections": ["sentinel-s2-l2a-cogs"], # Make sure to query only sentinel-2 COGs collection
      "datetime": datetime,
      "limit": limit, # max limit is 10000, default is 10
      "query": {
          "eo:cloud_cover": {
              "lt": cloudcover
          }  # Use low cloud cover
      },
      "bbox": bbox,
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
  #     thumbs = [f["assets"]["thumbnail"]["href"] for f in search["features"]]
  # print(search['numberReturned'], "items found")
  print("search - dates:", dates)
  print("search - features:", len(search["features"]))
  return search


def download(file, bbox, buffer=0, scale_factor=0):
  bbox_crs = CRS.from_epsg("4326")
  with rasterio.open(file) as src:
      # bounds (left, bottom, right, top)
      bounds = transform_bounds(bbox_crs, src.crs, *bbox)
      if buffer > 0:
          bounds = (bounds[0]-buffer, bounds[1]-buffer, bounds[2]+buffer, bounds[3]+buffer)
      w = win.from_bounds(*bounds, src.transform)
      if scale_factor != 0:
        res_window = win.Window(w.col_off * scale_factor, w.row_off * scale_factor,
                    w.width * scale_factor, w.height * scale_factor)
        img = src.read(1,
                out_shape=(
                    src.count,
                    int(res_window.height),
                    int(res_window.width)
                ),
                resampling=Resampling.bilinear,
                masked=False,
                window=w
            )
        t = win.transform(w, src.transform)
        tr = t * t.scale((w.width/res_window.width),(w.height/res_window.height))
        return img, src.meta.copy(), tr

      img = src.read(1, window=w)
      return img, src.meta.copy(), win.transform(w, src.transform)

    
def save(out_image, out_meta, out_transform, dir, filename):
  if dir:
    os.makedirs(dir, exist_ok=True)
    filename = dir + "/" + filename
  kwargs = out_meta
  kwargs.update({'driver': 'GTiff', 'height': out_image.shape[0],
                    'width': out_image.shape[1], 'transform': out_transform, 'dtype': rasterio.float32})
  with rasterio.open(filename, 'w', **kwargs) as dst:
      dst.write_band(1, out_image.astype(rasterio.float32))

def find_files(assets, bands):
  li = []
  for a in assets["features"]:
    asset = a["assets"]
    for b in bands:
        li.append(asset[b]["href"])
  return li

if __name__ == '__main__':
  bbox = [-7.754594852215678,40.3226711552789,-7.715919971356005,40.3394747419913]
  assets = search(bbox, "2021-03-19T00:00:00Z/2021-03-22T00:00:00Z", cloudcover=20, limit=20)
  bands = ["B02","B03","B04","B08","B11","B12"]
  files = find_files(assets, bands)
  print("Number of files:", len(files))
  
  fire_date = "2021-03-18_"
  for f in files:
    s = f.split("/")
    b = s[10].split(".")[0]
    scale = 0
    if b == "B11" or b == "B12":
      scale = 2
    img, meta, tf = download(f, bbox, buffer=50, scale_factor=scale)
    name = fire_date+s[9]+"_"+s[10]
    save(img, meta, tf, "/mnt/box/julia/burnedareasBbox", name)
    print(name, "downloaded successfully")