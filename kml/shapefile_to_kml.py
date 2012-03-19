
import os, sys, pdb
from pygis.shapefile.shapefile_utilities import get_shapefile_data
from pygis.kml.kml_utilities import make_kml

class Shapefile_To_Kml:

    """
    Summary: This class converts an ArcGIS shapefile to a kml. This only works for 
    point and polygon shapefiles.  The geometry type (i.e. point or polygon) is detected and the
    proper method is invoked. The output is a kml named the same as
    the shapefile.
    
    'shapeFilePath' - The path to the shapefile. For example:

        C:\UserFiles\Path\To\file\file.shp

    'outFolderPath' - The path to the folder where you want the kml to be
    saved. For example:

        C:\UserFiles\Path\To\file

    """

    def __init__( self, shapeFilePath, outFolderPath ):

        self.shapeFilePath = shapeFilePath
        self.outFolderPath = outFolderPath

    def to_kml( self ):

        """
        Summary:  This method opens an ESRI shapefile and extracts all the
        vertices for every feature (point, polygon), attribute table data names and
        attribure table row data.  All this data is packaged in a bundle (a
        list) and passed to a generate kml method.  The method automatically
        detects the geometry type (point or polygon) and passes it to the
        proper 'make kml' method.

        """

        # calls a method in shapefile_utilities that grabs the shapefile's
        # coordinates, attribute columns, attribute row data and other information.
        kmlPacket = get_shapefile_data( self.shapeFilePath )

        self.kmlBundle = kmlPacket[0] 
        self.attributeColumns = kmlPacket[1] 
        self.coordHolder = kmlPacket[2] 
        self.geomTracker = kmlPacket[3] 
        self.fileRoot = kmlPacket[4]
        
        # calls method from pygis.kml.kml_utilities. The kwarg 'fromShapefile' HAS to be set to 'True'.
        make_kml( 
                 self.outFolderPath, 
                 self.fileRoot + '.kml',    # kmlFileName 
                 self.kmlBundle[1:],        # bubbleFields 
                 self.geomTracker,          # bundle of data 
                 self.kmlBundle[0],
                 fromShapefile=True
                )

   
