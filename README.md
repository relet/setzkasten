# setzkasten

A simple tiler to align high resolution images on an infinite zoomable plane. 
The results can be displayed with any regular mapping client that supports
XYZ tiles.

The necessity for this approach evolved when I started taking (sometimes)
gigapixel photos through focus stacking and stitching microscopy images. It is a self-hosted alternative to commercial operations like zoomify or 
easyzoom. In addition it allows you to arrange multiple images on the same
plane. Currently this happens through the configuration files.

Self-hosting this type of map is made very affordable through static file
CDN caching as for example provided by cloudflare.

![Setzkasten example](/images/setzkasten.png)

An example viewer and configuration is provided.

**Configuration**

Configuration currently takes the form of a JSON file. The metadata is somewhat geared towards biological observations, but easy enough to change in the source code.

```
{
    "target": "/var/www/html/",
    "tilesize": 256,
    "maxzoom": 14,
    "sources": [
        ["filename.png", 65000, 210000, 18, "Title", "Family", "date", "location", "", "href"],
		...
}
```

Parameters:
* **target**: The image tiles will be generated into the folder `target/tiles`. A GeoJSON feature overview will be written to `target/features.geojson`.
* **tilesize**: The size of the cropped tiles.
* **maxzoom**: The maximum zoom level to generate. This can be set lower to generate faster previews.
* **sources**: An array with information about the image sources, in particular
  * Filename
  * Horizontal offset to the center of the plane (in pixels, relative to
    the specified zoom level. An 
    image provided with a zoom level one lower will only use half of the
    pixels to be placed at the same location)
  * Vertical offset to the center of the plane
  * Zoom level, at which the image will be written with its full pixel 
    extent. In lower zoom levels, the image will be scaled 50%, 25% etc. 
    Higher zoom levels are currently not written, but simulated through 
    the viewing client.
  * Title, etc.: Metadata that is written only to the GeoJSON file.

Each image in the sources array will be read in order. It will be split 
into tiles. Then for each tile, setzkasten will load an 
existing tile at this location (if it exists) and paste 
the tile data on top. Handling of transparency depends on 
the image formats.

Images late in the source array will be pasted over earlier images if 
they share the same location. 

Finally, for all images, a GeoJSON file with image extents and metadata
will be written to features.geojson. This file can be used to make the 
map more interactive.


**Example**

This is also the code behind my own (rather modest) entomological collection: 

**[setzkasten.relet.net](https://setzkasten.relet.net)**