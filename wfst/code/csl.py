import configparser
import urllib.request

""" GENERAL TODO
- We should try/except more
- is the "yield sleep(0.1) as short as it can be? Why not 0.01?
- more assertions :)
- unit tests!

- can we record all the events? crossbar can't (according to IRC) but maybe via meta-events and a subscriber to everything who logs?
"""

# Here are some common functions that did not belong elsewhere


def load_config() -> dict:
    """
    Parses our csl.ini file into a dict with proper data types
    :return: dict of config values
    """
    csl_config = configparser.ConfigParser()
    csl_config.read('csl.ini')  # TODO this path is NOT RELATIVE to pwd if run via crossbar, WTF!

    # path could be a parameter instead

    config = {}

    config['debug'] = bool(csl_config['DEFAULT']['debug'])

    config['gridsize'] = int(csl_config['DEFAULT']['gridsize'])

    config['realm'] = csl_config['DEFAULT']['realm']
    config['router'] = csl_config['DEFAULT']['router']
    config['ws_server'] = csl_config['DEFAULT']['ws_server']

    config['ows_url'] = csl_config['DEFAULT']['ows_url']


    return config


def grid_coordinates(bbox: tuple, gridsize: int) -> list:
    """
    Returns a matrix of gridsize with the real world coordinates of each cell's center
    :param bbox:
    :param gridsize
    :return:
    """
    x_min = bbox[0]
    y_min = bbox[1]
    x_max = bbox[2]
    y_max = bbox[3]

    cell_width = (x_max-x_min)/gridsize
    cell_height = (y_max-y_min)/gridsize

    # "array" gridsize*gridsize with a tuple (x, y) for each cell center's coordinates
    row = [None]*gridsize
    grid = []
    for i in range(gridsize):
        grid.append(list(row))  # list(list) trick to copy instead of reusing the list
        # see http://stackoverflow.com/questions/2612802/how-to-clone-or-copy-a-list-in-python

    for u in range(gridsize):
        for v in range(gridsize):
            x = x_min + cell_width/2 + (cell_width*u)
            y = y_min + cell_height/2 + (cell_height*v)
            grid[u][v] = (x, y)

    return grid


def bbox_to_wktpolygon(bbox: tuple) -> str:
    """ starting lower left, then clockwise. TODO is there a standard?"""
    x_min, y_min, x_max, y_max = bbox

    # using west south east north notation below because they are shorter...
    return "POLYGON (({w} {s}, {w} {n}, {e} {n}, {e} {s}, {w} {s}))".format(w=x_min, s=y_min, e=x_max, n=y_max)


def xy_to_wktpoint(x: float, y: float) -> str:
    return "POINT ({x} {y})".format(x=x, y=y)


def pretty_asciigrid(grid, gridsize: int) -> str:
    """
    Create an ASCII representation of a grid for printing/debugging
    :param grid:
    :param gridsize:
    :return: String
    """

    asciigrid = grid.astype(str)

    # Create one character per number
    asciigrid[asciigrid == "-1"] = "."
    # leave other numbers as they are
    asciigrid[asciigrid == "10"] = "A"
    asciigrid[asciigrid == "11"] = "B"
    asciigrid[asciigrid == "12"] = "C"
    asciigrid[asciigrid == "13"] = "D"
    asciigrid[asciigrid == "14"] = "E"
    asciigrid[asciigrid == "15"] = "F"

    # TODO turn ALL two-digit numbers into A-F, not just 10-15
    # there must be a better way

    asciilist = []
    # Since the grid starts at 0,0 "at its top left" but our origin is bottom left, we do it bottom up
    # TODO there must be a better way than this ugly range call
    for rowindex in range(gridsize-1, -1, -1):
        row = asciigrid[:, rowindex, :][0]  # full Nth row of this (1,gs,gs) array, [0] because the shape return is (1, gs) first
        asciilist.append("".join(row.astype(list)))

    asciistring = "\n".join(asciilist)
    return asciistring


def get_workshop() -> str:
    # TODOTODO url des servers auch in die config!
    with urllib.request.urlopen("http://www.example.com/workshop/get_current") as response:
        workshop = response.read()
        return workshop.decode("utf-8")

if __name__ == '__main__':
    config = load_config()
    print(config)
    print(get_workshop())
