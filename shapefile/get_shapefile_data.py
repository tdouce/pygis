import os, sys
from pygis.shapefile.shapefile_utilities import get_shapefile_data


class Shapefile_Data:

    """
    Summary: This class gets the basic information from a shapefile. It returns
    the vertices, attribute row data, attribute column names, etc.  It uses a
    module 'get_shapefile_data()' from shapefile_utilities.py. It automatically
    detects the geometery type (i.e. point or polygon). It does not support
    point shapefiles...yet.

    'shapeFilePath' - The path to the shapefile you want to inspect. For
    example:

        C:\UserFiles\To\Shapefile\test.shp

    """

    def __init__( self, shapeFilePath):

        self.shapeFilePath = shapeFilePath


    def get( self ):

        """
        This method pass the shapefilepath to a method in a module that returns
        all the needed data.  It uses the returned data to parse it
        appropriately for the geometery type (i.e point or polygon)

        """

        # the 'get_shapefile_data() method is called from the
        # 'shapefile_utilities' module. The returned data is assigned to a variable
        kmlPacket = get_shapefile_data( self.shapeFilePath )

        #  The packet of data is taken apart and the appropriate variables are assigned
        self.kmlBundle = kmlPacket[0] 
        self.attributeColumns = kmlPacket[1] 
        self.geomType = kmlPacket[3] 
        self.fileName = kmlPacket[4] + '.shp'
        self.vertices = []
        self.featureCount = ''
        self.attributeRowData = []
        coordHolder = kmlPacket[2]

        # Assigned proper attributes for point shapefiles
        if self.geomType == 'Point':
        
            self.vertices = [ x[:2] for x in coordHolder ]

            self.featureCount =  len( self.vertices )

            self.attributeRowData = [ x[2:] for x in coordHolder ]

            
        # Assigned proper attributes for polygon shapefiles
        elif self.geomType == 'Polygon':

            self.vertices = [ x[:-1] for x in coordHolder ]

            self.featureCount =  len( self.vertices )

            self.attributeRowData = [ x[-1:][0] for x in coordHolder ]

        # Exit if something didn't work or if the geometry type is a polyline, which isn't supported.
        else:

            print 'Something happend and there is an unexpected failure'
            sys.exit(1)

            
        

