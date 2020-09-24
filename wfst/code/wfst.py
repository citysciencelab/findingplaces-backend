from osgeo import ogr, osr
from time import time
from datetime import datetime

from os import environ

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks

from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner

from csl import load_config
from random import choice

import pickle
# from csl import get_workshop

# TODO benchmark if it would be faster if we kept the connection open forever and listen via WAMP
# or if we reconnect to the OWS server each time
# or if we just forge the HTTP requests ourselves...
# or if we always get the whole layer's data to local memory, operate on that and replace everything?

# This is quite horrible code.



def rc_to_xy(row: int, column: int, bbox: tuple, gridsize: int) -> tuple:
    """
    Transform u, v coordinates of the table to "real-world" coordinates
    # TODO what about the margins between the grid cells on the table?
    Assumptions: xy - Origin is at bottom left
                 uv - Origin is at top left
                 area is small enough that we can consider it a plane
    :param u: u coordinate
    :param v: v coordinate
    :param bbox: (left,bottom,right,top) of the real world bbox coordinates
    :param gridsize: number of uv cells of the (square) table
    :return: x, y
    """

    # rounding down to meters
    digits = 0 # TODO in csl.ini

    x_min = bbox[0]
    y_min = bbox[1]
    x_max = bbox[2]
    y_max = bbox[3]

    # calculate and round the lengths of the sides
    x_range = x_max - x_min
    #x_range = round(x_range, digits)
    y_range = y_max - y_min
    #y_range = round(y_range, digits)

    assert x_range > 0
    assert y_range > 0
    # I originally assumed our real world bbox would be square
    # but of course that is not the case if the map in the browser
    # is square in a different CRS than the bbox we output from it
    # right now we use a map in 3857/900913 but a 25832 BBOX
    # assert x_range == y_range

    cell_width = x_range / gridsize
    cell_height = y_range / gridsize

    # start at the minima
    # add half a cell as we want to get the cell centers
    # add u/v cell widths/heights
    x = x_min + cell_width / 2 + (cell_width * column)
    y = y_max - cell_height / 2 - (cell_height * row)  # minus because uv is topleft, xy is topright

    #    if debug:
    #        print("u, v -> x, y: {u} {v} -> {x} {y}".format(u=u, v=v, x=x, y=y))

    return x, y


def insert_point(coordinates: tuple, value: int) -> (str, int):
    """
    insert point to sessionlayer, return flurstueck_kennzeichen and current inhabitants
    we get 3857 from OL and use 25832 for this layer at CSL
    :param coordinates:
    :param value:
    :return: flurstueck_kennzeichen, current inhabitants
    """

    if debug:
        start_time = time()
        print("DEBUG: Start: {}".format(start_time))

    # First create a proper geometry
    brick_point = ogr.CreateGeometryFromWkt("Point ({x} {y})".format(x=coordinates[0], y=coordinates[1]))  # TODO is creating from WKT reasonable? feels stupid...

    # Then transform it from 3857 to 25832
    # aus cookbook
    source = osr.SpatialReference()
    source.ImportFromEPSG(3857)
    target = osr.SpatialReference()
    target.ImportFromEPSG(25832)
    transform = osr.CoordinateTransformation(source, target)
    brick_point.Transform(transform)
    print("Point in 25832: {}".format(brick_point))

    x25832 = brick_point.GetX()  # Get X coordinates
    y25832 = brick_point.GetY()  # Get Y coordinates

    # now we have super accurate sub millimeter coordinates again, so ...
    # x and y are rounded to the meter because we won't to get in any "this feature was 3 nanometers to the left" mess
    x25832 = round(x25832, 0)
    y25832 = round(y25832, 0)
    brick_point = ogr.CreateGeometryFromWkt("POINT ({x} {y})".format(x=x25832, y=y25832))
    print("New point is:", brick_point)
    # TODO surely above could be drastically simplified by transforming the coordinates first, then only creating ONE geometry...

    # We have our new geometry, let's get the appropriate layer via WFS
    # TODO nicht in der funktion, sondern in der klasse vorhalten!!?
    driver = ogr.GetDriverByName("WFS")
    wfs = driver.Open(wfs_url, update=1)  # 1 means writable
    sessionlayer = wfs.GetLayerByName("unterkuenfte")

    if debug: print("DEBUG: Session layer gotten: {}".format(time()-start_time))

    # If there is an existing feature at the same coordinates, we want to update that feature
    # spatial filter "reduces" our working "copy" of the layer to just the intersecting(?) features
    # TODOTODO we would not need to spatial filter if we would track if a change happened from "-1 to code" or "code to code"
    sessionlayer.SetSpatialFilter(brick_point)
    num_intersecting_features = len(sessionlayer)
    assert num_intersecting_features <= 1  # there should be only one feature now or none
    # we might get duplicates due to bugs or race conditions maybe, best way would be to remove all

    # If there is an intersection, we update an existing feature or delete it
    # otherwise we create a new one
    if num_intersecting_features >= 1:
        feature = sessionlayer.GetNextFeature()

        if value == 0:
            # our change was a removal
            print("INFO: Deleting feature with ID {}".format(feature.GetFID()))
            sessionlayer.DeleteFeature(feature.GetFID())  # delete  # TODO igitt, beim iterieren löschen? ...
            del feature, sessionlayer, wfs
            return None, None # we are not interested in the affected flurstück nor the value
        else:
            print("INFO: Updating feature with ID {}".format(feature.GetFID()))
            feature.SetField("platz", value)
            feature.SetField("status", 0)
            #feature.SetField("timestamp", datetime.now()) # TODO this should use UTC, not local timestamp. also in table schema...
            sessionlayer.SetFeature(feature)
            if debug: print("DEBUG: Feature updated: {}".format(time()-start_time))
            del sessionlayer, wfs # TODOTODO del feature? return? 8)
            return feature.fsk, value


    else:
        # This feature is a new feature

        if value == 0:
            # Somehow we got a deletion even though there was no existing feature, let's just skip this then
            del sessionlayer, wfs
            return None, None

        # Which Flurstück are we in?
        flurstuecke = wfs.GetLayerByName("flurstuecke")
        flurstuecke.SetSpatialFilter(brick_point)
        assert len(flurstuecke) <= 1 # we should just get one flurstück or none at all

        if len(flurstuecke) > 0:
            if debug: print("DEBUG: Flurstück found: {}".format(time()-start_time))
            flurstueck = flurstuecke.GetNextFeature()
            if not flurstueck:
                if debug: print("DEBUG: No Flurstück found: {}".format(time()-start_time))
                return None, None

            flurstueck_kennzeichen = flurstueck.fsk  # GetField("fsk") == .fsk :))
        else:
            if debug: print("DEBUG: No Flurstück found: {}".format(time()-start_time))
            del flurstuecke, sessionlayer, wfs
            return None, None

        # Create the feature and set its attributes
        feature = ogr.Feature(sessionlayer.GetLayerDefn())

        feature.SetGeometry(brick_point)
        feature.SetField("platz", value)
        feature.SetField("fsk", flurstueck_kennzeichen)
        feature.SetField("status", 0)
        # timestamp is added db-side due to the table schema # TODOTODO nope, not through wfs for some reason?!
        #feature.SetField("timestamp", datetime.now()) # TODO this should use UTC, not local timestamp. also in table schema...
        # TODOTODOTODO ^
        # feature.SetField("workshop", workshop)  # global can be read without declaring it global here :)

        if debug:
            print(feature.DumpReadable())
            print("DEBUG: ^ Feature ready: {}".format(time()-start_time))

        # Add the feature to the layer
        sessionlayer.CreateFeature(feature)  # you MUST have the same geometry type as the layer is or it will silently drop the geometry

        if debug: print("DEBUG: Feature added: {}".format(time()-start_time))

    del flurstueck, flurstuecke, sessionlayer, wfs  # TODO do i really need this?

    return flurstueck_kennzeichen, value


class Component(ApplicationSession):

    config = load_config()
    gridsize = config['gridsize']
    bbox = ()

    pause = False  # to pause accepting changes

    @inlineCallbacks
    def onJoin(self, details):
        print("session attached")
        sub_changes = yield self.subscribe(self.on_event_changes, 'changes')
        print("Subscribed to changes with {}".format(sub_changes.id))
        sub_bbox = yield self.subscribe(self.on_event_bbox, 'bbox')
        print("Subscribed to bbox with {}".format(sub_bbox))
        sub_sessionlayer = yield self.subscribe(self.on_event_sessionlayer, 'sessionlayer')
        print("Subscribed to sessionlayer with {}".format(sub_sessionlayer))

    def on_event_sessionlayer(self, event):
        """
        Allows to pause WFST edits and bbox updates
        Changes should not propagate here anyways when paused but bbox updates need to be ignored
        :param event:
        :return:
        """
        if event == "pause":
            print("INFO: Pausing WFST")
            self.pause = True
        elif event == "unpause":
            print("INFO: Unpausing WFST")
            self.pause = False

    def on_event_bbox(self, x0, y0, x1, y1):
        print("INFO: Got a bbox: {}".format((x0, y0, x1, y1)))
        self.bbox = (x0, y0, x1, y1)
        # yes, also if paused! especially then!

    def on_event_changes(self, changes):

        if self.pause:
            print("INFO: Ignoring changes, we are paused!")
            return None

        if not self.bbox:
            print("WARNING: Ignoring changes, we don't know the BBOX yet!")
            return None

        # global workshop
        # if not workshop:
        #     workshop = get_workshop()

        changes = pickle.loads(changes)
        print("INFO: Changes {}".format(changes))

        for change in changes:
            row = int(change[1])    # changes come as (x,y,code)
            column = int(change[0])
            code = int(change[2])
            x, y = rc_to_xy(row, column, self.bbox, self.gridsize)
            print(x, y, code)

            # falls code = -1 -> get_fsk, delete feature at coordinate, recalculate sum(inhabitants) des flurstücks
            # sonst update/create feature at coordinate, get_fsk, recalculate sum(inhabitants) des flurstücks

            flurstueck_kennzeichen, gesetzte_plaetze = insert_point((x, y), code)
            if flurstueck_kennzeichen is None and gesetzte_plaetze == -1:
                # investigatorbrick :)
                continue

            print('publishing flurstueck', (flurstueck_kennzeichen, gesetzte_plaetze))
            self.publish('flurstueck', (flurstueck_kennzeichen, gesetzte_plaetze))

            # TODO race condition? wenn wir hier nicht schnell genug sind,
            # kommen dann schnell aufeinanderfolgende changes rein?!
            # TODOTODO das führt dazu, dass sich eine queue aufbaut... wird immer länger bis geoserver ram probleme bekommt

        # print('publishing sessionlayer', "update (wfst)")
        # self.publish('sessionlayer', "update")

    # def onDisconnect(self):
    #     print("disconnected")
    #     if reactor.running:
    #         reactor.stop()


if __name__ == '__main__':
    print("loading cfg...")
    config = load_config()
    realm = config['realm']
    router = config['router']
    ws_server = config['ws_server']

    global wfs_url
    wfs_url = config['ows_url']
    debug = config['debug']

    print("running runner...")
    runner = ApplicationRunner(
        environ.get(router, ws_server),
        realm
    )
    runner.run(Component)
