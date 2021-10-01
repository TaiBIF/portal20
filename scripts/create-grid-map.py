import numpy as np
import bisect

# x: longtitude, y: latitude

list_x = np.arange(-180, 180, 0.01)
list_y = np.arange(-90, 90, 0.01)
def convert_grid_to_coor(grid_x, grid_y):
  center_x = (list_x[grid_x] + list_x[grid_x+1])/2
  center_y = (list_y[grid_y] + list_y[grid_y+1])/2
  return center_x, center_y

# x_grid = bisect.bisect(list_x, grid_x)-1
# y_grid = bisect.bisect_right(list_y, grid_y)-1

def convert_coor_to_grid(x, y):
  grid_x = bisect.bisect(list_x, x)-1
  grid_y = bisect.bisect_right(list_y, y)-1
  return grid_x, grid_y

# update current csv
import pandas as pd
import os
import glob

path = './solr-workspace/conf-taibif-occur/taibif_occurrence/'
extension = 'csv'
file_list = glob.glob('{}*.{}'.format(path,extension))

for j in file_list:
  print(j)
  df = pd.read_csv(j, dtype={'kingdom_key': 'object','order_key':'object','phylum_key':'object',
                             'species_key': 'object', 'class_key': 'object', 'family_key':'object',
                             'genus_key': 'object', 'month': 'object', 'year': 'object', 'day':'object'})
  df['grid_x'] = -1
  df['grid_y'] = -1
  # for i in range(len(df)):
  for i in range(len(df)):
    if not pd.isna(df.iloc[i].latitude) and not pd.isna(df.iloc[i].longtitude):
      grid_x, grid_y = convert_coor_to_grid(df.iloc[i].longtitude, df.iloc[i].latitude)
      df.iloc[i, df.columns.get_loc('grid_x')] = grid_x
      df.iloc[i, df.columns.get_loc('grid_y')] = grid_y
  df = df.drop(columns=['location_rpt'])
  df.to_csv(f'{path}{j[-7:-4]}_grid.csv',index=False)

