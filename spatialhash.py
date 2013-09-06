#!/usr/bin/python2.4

import sys
import math

localfloor = math.floor

class SpatialHash3D:

    # Optimized version of SpatialHash for three dimensional space
    # Optimizations work by assuming the following:
    #	The space is three dimensional;
    #	The area of a quadrant is r*r*r and r is always used as the radius for searching. This allows us to write a simple loop of the quadrants surrounding the position.
    def __init__(self, size):

        self.size = size
        self.quads = {}

    def quadkey(self, position):
        msize = self.size
        return (int(localfloor(position[0]/msize)), int(localfloor(position[1]/msize)), int(localfloor(position[2]/msize)))

    # Avoids the overhead of tuple creation
    def quadkeyxyz(self, posx, posy, posz):
        msize = self.size
        return (int(localfloor(posx/msize)), int(localfloor(posy/msize)), int(localfloor(posz/msize)))

    def insert(self, position, data):
        key = self.quadkey(position)
        mquads = self.quads
        mquads[key] = mquads.get(key, []) + [(position, data)]

    def nearby(self, position):

        radius = self.size
        radiussquared = radius * radius

        # Search all quadrants surrounding the position (a 3*3*3 cube with position in the center)
        minkey = self.quadkeyxyz(position[0] - radius, position[1] - radius, position[2] - radius)
        minx, miny, minz = minkey[0], minkey[1], minkey[2]

        results = []

        mquads = self.quads
        for x in xrange(minx, minx + 3):
            for y in xrange(miny, miny + 3):
                for z in xrange(minz, minz + 3):
                    quadrant = mquads.get((x, y, z))
                    if quadrant:
                        for pos, data in quadrant:
                            distsquared = ((position[0] - pos[0]) ** 2) + ((position[1] - pos[1]) ** 2) + ((position[2] - pos[2]) ** 2)
                            if distsquared <= radiussquared:
                                results += [(pos, data)]

        return results

# todo 29: Remove this in favor of SpatialHash3D
class SpatialHash:

    def __init__(self, size):

        self.size = size
        self.dimensions = 0
        self.quads = {}

    def quadkey(self, position):

        if len(position) != self.dimensions:
            sys.exit()

        quadrant = [0.]*self.dimensions
        for i in xrange(self.dimensions):
            quadrant[i] = int(math.floor(position[i]/self.size))

        return tuple(quadrant)

    def insert(self, position, data):

        if self.dimensions == 0:
            self.dimensions = len(position)

        key = self.quadkey(position)
        self.quads[key] = self.quads.get(key, []) + [(position, data)]

    def nearby(self, position, radius):

        minkey = self.quadkey([position[i] - radius for i in xrange(self.dimensions)])
        maxkey = self.quadkey([position[i] + radius for i in xrange(self.dimensions)])

        quadstosearch = [[i] for i in range(minkey[0], maxkey[0]+1)]

        for i in xrange(1, self.dimensions):
            newquads = []
            for j in xrange(minkey[i], maxkey[i]+1):
                newquads += [oldquad + [j] for oldquad in quadstosearch]
            quadstosearch = newquads

        radiussquared = radius*radius

        results = []
        for quad in quadstosearch:
            quadrant = self.quads.get(tuple(quad))
            if quadrant:
                for pos, data in quadrant:
                    distsquared = 0
                    for i in xrange(self.dimensions):
                        distsquared += (position[i] - pos[i]) ** 2
                    if distsquared <= radiussquared:
                            results += [(pos, data)]

        return results

if __name__ == "__main__":

    foo = SpatialHash(2)

    foo.insert((0., 0., 0.), "A")
    foo.insert((0., 1., 4.), "B")
    foo.insert((0., 5., 6.), "C")
    foo.insert((1., 1., 8.), "D")

    print repr(foo.quads)

    print repr(foo.nearby((0., 0., 0.), 5))
