import numpy as np

list_x = np.arange(-180, 180, 0.01)
list_y = np.arange(-90, 90, 0.01)

def convert_grid_to_coor(grid_x, grid_y):
    # deal with exception
    if grid_x >= 35999:
        grid_x = 35998
    if grid_y >= 17999:
        grid_y = 17998
    center_x = (list_x[grid_x] + list_x[grid_x+1])/2
    center_y = (list_y[grid_y] + list_y[grid_y+1])/2
    return center_x, center_y
