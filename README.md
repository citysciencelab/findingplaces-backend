# FindingPlaces Backend
Finding Places was a cooperation project of the HafenCity University and the City of Hamburg. In the period from May 26thto July 15th2016 the people of Hamburg were – in numerous participatory workshops with FindingPlaces CityScopes – searching for public areas suitable for the construction of accommodation for refugees. The task: to find areas which allow the accommodation of 20,000 refugees in total.

https://user-images.githubusercontent.com/36763878/161037708-c9f8709b-7abd-47fe-b10c-bf613f0f19ea.mp4

The project aimed to encourage a city-wide dialogue on how and where to find accommodation for a large group of refugees arriving in Hamburg. At the same time, it showcased the complexity of planning processes and thus helped develop an increased acceptance within the civil society. This led to a rewarding combination of the participants’ local knowledge and the expertise of the authorities and science. The participatory workshops not only led to the discussion of specific locations, but rather encouraged a discourse in the context of different interests (living / industry / maintenance) and legal planning requirements.  

[Project Website (in German)](https://findingplaces.hamburg/)

[Results brochure (in English)](https://repos.hcu-hamburg.de/handle/hcu/488)

[Publication: Finding Places: HCI Platform for Public Participation in Refugees’ Accommodation Process](https://www.researchgate.net/publication/319445941_Finding_Places_HCI_Platform_for_Public_Participation_in_Refugees%27_Accommodation_Process)


This is the backend code used for FindingPlaces  

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
