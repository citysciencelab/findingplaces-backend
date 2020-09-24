This is the backend code used for FindingPlaces  
https://www.findingplaces.hamburg/

Grid coordinates in the are transformed to real world coordinates and send to a GeoServer  
instance using WFS-T. Plus some other stuff.

# Warning
This is not meant for you to simply clone and run, there are several other  
components that you would need to setup (e.g. a WFS server, Postgres with the  
tables, etc). Just feel free to read through it to verify that no one  
manipulated things maliciously. 

# Dependencies
- Python 3
- autobahn
- psycopg2
- osgeo/gdal

Bleeding edge versions were used.

-----

You are likely to be eaten by a grue.

# Todo
* [ ] write this readme
* [X] deploy on FP-PC
* [ ] clean up code
* [ ] comment code