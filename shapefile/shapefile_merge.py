import os, pdb, datetime, itertools, sys
from pygis.shapefile.get_shapefile_data import Shapefile_Data
from pygis.shapefile.shapefile_utilities import make_shapefile_polygon_esri_v9
from pygis.shapefile.metadata import Write_Metadata, make_shapefile_metadata


class Shapefile_Merge:

    def __init__(self, inFolder, outFolder, merge_file_name, coordsys ):

        self.inFolder = inFolder
        self.outFolder = outFolder
        self.merge_file_name = merge_file_name
        self.coordsys = coordsys
        print 'Script not completed'
        sys.exit(1)



    def merge(self, metadata=None ):

        shapefiles = os.listdir( self.inFolder )

        bundle_Polygon = []
        attribute_columns = []
        shapefile_counter = 0
        gis_id_counter = 0

        for shapefile in shapefiles:

            shapefile_package_Polygon = []

            if shapefile.endswith('.shp'):

                print
                print '******'
                print

                ins = Shapefile_Data( os.path.join( self.inFolder, shapefile) )
                ins.get()

                '''
                print 'geom: ', ins.geomType
                print 'fileName: ', ins.fileName
                print 'Vertices: ', ins.vertices
                print 'FeatureCount: ', ins.featureCount
                print 'Attributes: ', ins.attributeRowData
                '''
                print 'Attribute Columns: ', ins.attributeColumns

                querys = ins.attributeRowData
                headers = ins.attributeColumns
                coordinates = ins.vertices

                if ins.geomType == 'Polygon':

                    '''
                    superCoordListName = [ self.merge_file_name ]
                    
                    toGisSuperList = [([query] + coordinates[index]) for index,query in enumerate(querys)]

                    if shapefile_counter >= 1:
                        bundle_Polygon[0][2].insert( len(bundle_Polygon[0][2]), toGisSuperList[0] )

                    else:
                        shapefile_package_Polygon.append( superCoordListName )
                        shapefile_package_Polygon.append( attributeColumns )
                        shapefile_package_Polygon.append( toGisSuperList )

                        bundle_Polygon.append( shapefile_package_Polygon )
                    '''

                    shapefile_counter += 1

                    attribute_columns.append( headers )
        
        headers_prep = list( itertools.chain( *attribute_columns ) )


        '''
        if len( bundle_Polygon) >= 1:

            make_shapefile_polygon_esri_v9( bundle_Polygon, self.outFolder, self.coordsys )

            # Dictionary of of metadata content we want to assign each shapefiles's
            # metadata. This will be viewable in ArcCatalog

            if metadata is not None:
                
                metadataDict = metadata

                # Building path to the xml file that will be worked on
                xmlFilePath = os.path.join( self.outFolder, self.merge_file_name + '.shp.xml')

                make_shapefile_metadata( xmlFilePath,  metadataDict )
        '''



