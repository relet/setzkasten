#!/usr/bin/env python3

import cv2 as cv
import json
import math
import numpy as np
import os
import sys

config = json.load(open("config.json","r"))

target = config.get('target')
tilesize = config.get('tilesize')

# pixel coordinates as x,y
# tile coordinates as t,u

for source in config.get('sources',[]):
    xrel, yrel, zoom = source[1:4]

    print(source)

    # relative zero (center) at the defined zoom level
    x0 = math.floor(tilesize * math.pow(2, zoom-1))
    y0 = math.floor(tilesize * math.pow(2, zoom-1))

    # image coordinates at that zoom level
    xi, yi = x0 + xrel, y0 + yrel

    # image size
    source_im = cv.imread(source[0])
    w,h = source_im.shape[:2]
    wt = math.ceil(w / tilesize)
    ht = math.ceil(h / tilesize)

    # first tile to consider
    t0 = math.floor(xi / tilesize)
    u0 = math.floor(yi / tilesize)

    # top left of the considered tile
    xA = t0 * tilesize
    yA = u0 * tilesize

    # offset of the image to the first tile
    off_x = xi - xA
    off_y = yi - yA

    # TODO: scale and tile for all lower zoom levels

    for tx in range(0, wt):
        for ty in range(0,ht):
            # read current background tile
            folder   = target+"/"+str(zoom)+"/"+str(u0+ty)
            tile_url = folder +"/"+str(t0+tx)+".jpg"
            print("Loading "+tile_url)

            white_tile = np.zeros([tilesize, tilesize, 3],dtype=np.uint8)
            white_tile.fill(255)

            bg = cv.imread(tile_url)
            if bg is None:
                bg = white_tile.copy()
            # cut relevant section of source_im
            from_x = max(0, tx * tilesize - off_x)
            from_y = max(0, ty * tilesize - off_y)
            to_x   = min(w, (tx+1) * tilesize - off_x)
            to_y   = min(h, (ty+1) * tilesize - off_y)
            cutout = source_im[from_x:to_x, from_y:to_y]
            # correct location of background
            dest_x = max(0, off_x - tx * tilesize)
            dest_y = max(0, off_y - ty * tilesize)
            dto_x = dest_x + to_x - from_x
            dto_y = dest_y + to_y - from_y

            # TODO: treat source image as having white as transparency
            # paste cutout onto background
            bg[dest_x:dto_x, dest_y:dto_y] = cutout

            # then write that tile to file
            print("Writing ",tile_url)
            try:
                os.makedirs(folder)
            except:
                pass
            cv.imwrite(tile_url, bg)
