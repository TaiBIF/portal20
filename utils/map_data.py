import numpy as np
import bisect
import requests

list_x = np.arange(-180, 180, 0.01)
list_y = np.arange(-90, 90, 0.01)

def convert_grid_to_coor(grid_x, grid_y):
    # deal with exception
    if grid_x >= 35999:
        grid_x = 35998
    if grid_y >= 17999:
        grid_y = 17998
    center_x = round((list_x[grid_x] + list_x[grid_x+1])/2, 2)
    center_y = round((list_y[grid_y] + list_y[grid_y+1])/2, 2)
    return center_x, center_y

def convert_coor_to_grid(x, y):
  grid_x = bisect.bisect(list_x, x)-1
  grid_y = bisect.bisect(list_y, y)-1
  return grid_x, grid_y

def convert_x_coor_to_grid(x):
  grid_x = bisect.bisect(list_x, x)-1
  return grid_x

def convert_y_coor_to_grid(y):
  grid_y = bisect.bisect(list_y, y)-1
  return grid_y


def get_geojson(solr_url):
    facet_pivot_map = 'facet.pivot=grid_x,grid_y'
    if 'grid_x' in solr_url:
        map_url = f'{solr_url}&rows=0&facet=true&{facet_pivot_map}&facet.limit=-1'
    else:
        map_url = f'{solr_url}&rows=0&facet=true&fq=grid_x%3A%5B0%20TO%20*%5D&fq=grid_y%3A%5B0%20TO%20*%5D&{facet_pivot_map}&facet.limit=-1'    
    r = requests.get(map_url)
    map_geojson = {"type": "FeatureCollection", "features": []}

    if r.status_code == 200:
        data_c = r.json()['facet_counts']['facet_pivot']['grid_x,grid_y']
        map_geojson['features'] = [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": convert_grid_to_coor(i['value'], j['value'])},
                "properties": {"counts": j['count']}
            }
            for i in data_c for j in i['pivot']
        ]
    return map_geojson