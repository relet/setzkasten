#!/usr/bin/env python3

import cv2 as cv
import json
import math
import numpy as np
import os
import sys

from geojson import FeatureCollection, Feature, Polygon, dumps

config = json.load(open("config.json","r"))

target = config.get('target')
tilesize = config.get('tilesize')
maxzoom = config.get('maxzoom')

tile_format = '.webp'

LLBOUNDS = [-180.0, 180.0, -180.0, 180.0]

match = None
if len(sys.argv)>=2:
    match = sys.argv[1]

# pixel coordinates as x,y
# tile coordinates as t,u

def xy_to_latlon(x,y,zoom):
    max_x = -float(math.pow(2,zoom-1) * tilesize)
    lat = x / max_x * LLBOUNDS[1]
    max_y = float(math.pow(2,zoom-1) * tilesize)
    lon = y / max_y * LLBOUNDS[3]
    return lat,lon

features = []

for source in config.get('sources',[]):
    if len(source)<7:
        continue
    filename, xrel, yrel, imgzoom, title, family, date, location, comment, href = source[:10]

    print("Processing ",filename)
    source_im = cv.imread(filename, cv.IMREAD_UNCHANGED)

    # might be off by a factor off two, to be verified.
    if title:
        print(title)
        w,h = source_im.shape[:2]
        print("PIXEL COORDINATES ", xrel, yrel, xrel+w, yrel+h)
        left, top = xy_to_latlon(xrel, yrel, imgzoom)
        right, bottom = xy_to_latlon(xrel+w, yrel+h, imgzoom)
        poly = Polygon([[(top, left), (top, right), (bottom, right), (bottom, left), (top, left)]])
        feat = Feature(geometry=poly, properties = {
            "title":   title,
            "family":  family,
            "date":    date,
            "loc":     location,
            "comment": comment,
            "href":    href
        })
        features.append(feat)
        print(dumps(FeatureCollection(features), indent=2))
        #sys.exit(1)

    #if imgzoom < maxzoom:
    #    factor = math.pow(2, maxzoom-imgzoom)
    #    source_im = cv.resize(source_im, (0, 0), fx=factor, fy=factor)
    # FIXME: memory issues when blowing up - add maxzoom (and minzoom) to define display range

    if match and not match in filename:
        continue

    zoom = imgzoom
    w = h = 256 # just to pass the first check

    while zoom > 1 and w > 2 and h > 2:
      if zoom <= maxzoom:

        # relative zero (center) at the defined zoom level
        x0 = math.floor(tilesize * math.pow(2, zoom-1))
        y0 = math.floor(tilesize * math.pow(2, zoom-1))

        # image coordinates at that zoom level
        xi, yi = x0 + xrel, y0 + yrel

        # image size
        # NOTE: source images should always be transparent png, or overlaps will be covered
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

        off_t = math.floor(off_x / tilesize)
        off_u = math.floor(off_y / tilesize)

        # CHECK: adjust range to actually cover the location of the translated image
        folders={}
        for tx in range(0, wt+1):  # TODO: try t0-t0+wt
            for ty in range(0, ht+1):
                # read current background tile
                folder   = target+"tiles/"+str(zoom)+"/"+str(u0+ty)
                tile_url = folder +"/"+str(t0+tx)+tile_format
                #print("Loading "+tile_url)

                white_tile = np.zeros([tilesize, tilesize, 4],dtype=np.uint8)
                #white_tile.fill(255)

                bg = cv.imread(tile_url, cv.IMREAD_UNCHANGED)
                if bg is None:
                    bg = white_tile.copy()
                bg = cv.cvtColor(bg, cv.COLOR_BGR2BGRA)

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

                # paste cutout onto background
                # TODO: actually paste, not overwrite
                # eg. overwrite white_tile, then merge with bg

                try:
                    bg[dest_x:dto_x, dest_y:dto_y] = cutout
                except:
                    continue
                    #print("SOMETHING FAILED")
                    #cv.imshow('BG',bg)
                    #print("CUTOUT SIZE:", (from_x, to_x, from_y, to_y))
                    #print("FROM Y:", (from_y))
                    #print("TO Y:", (to_y))
                    #print("H:", h)
                    #cv.waitKey(1)
                    #sys.exit(1)

                # then write that tile to file
                if not folder in folders:
                  print("Writing ",folder)
                  try:
                    os.makedirs(folder)
                    folders[folder]=True
                  except:
                    pass
                cv.imwrite(tile_url, bg)

      zoom = zoom - 1
      xrel = math.floor(xrel / 2)
      yrel = math.floor(yrel / 2)
      source_im = cv.resize(source_im, (0, 0), fx=0.5, fy=0.5)
      w = math.floor(w / 2)
      h = math.floor(h / 2)

fc = FeatureCollection(features)
fp = open(target+"features.geojson", "w")
fp.write(dumps(fc))
fp.close()
