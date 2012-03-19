import xml.etree.cElementTree as etree
from xml.parsers.expat import*
from pygis.shapefile.metadata import make_shapefile_metadata
from pygis.shapefile.shapefile_utilities import make_shapefile_point_esri_v9, make_shapefile_polygon_esri_v9, putBackLegals, sanitize_filename, sanitize_header
import os, sys, pdb

def geom_checker( et, ns, geomTypes, geom_text ):

    """
    General function used to check the geometry type of a kml
    """

    # xpath to the first point node
    geom_check = et.find('{%s}Document/{%s}Placemark/{%s}%s' % ( ns, ns, ns, geom_text ) ).tag.split('}')[1]

    # Add to 'geomTypes' container
    geomTypes.append( geom_check )



def package_for_make_shapefile( feature, geomType ):

    # Document name
    docName = feature[0][0]

    # THE '_' SHOULD NOT BE CHANGED because the zip_it() method relies
    # on this delimiter to package the zipfiles genreated from kmls
    point_appending = '_' + geomType

    docName = [ docName[0] + point_appending ]

    # Attribute row columns
    attrHead = feature[0][1]

    # Coords
    superCoordList = feature[0][2]

    # Sanitize for non-permitted characters in filename 
    docName = sanitize_filename( docName[0], '__' )

    # Sanitize for non-permitted characters and length in attrHead
    attrHead = sanitize_header( attrHead, '__' )

    return [docName], superCoordList, attrHead, point_appending


def get_doc_name_placemarks( et, ns ):
        
    # Get the document name from the kml
    docName = [ et.find('{%s}Document/{%s}name' % ( ns, ns) ).text.split('.')[0] ]

    # Find all the placemarks in the kmkl
    Placemarks = et.findall('{%s}Document/{%s}Placemark' % (ns,ns))

    return docName, Placemarks


def get_coords( child, searchNode ):

    """
    This is a recursion function that is invoked to get the coordinates for a
    placemark.  Although the tree structure varies from point and polygon
    nodes, this recursion function will ge the coordinates

    child - The child node, this is passed in each time with each iteration. 

    searchNode - This is the name of the node that you are searching for.  In
    our case we are searching for the 'coordinate' node. For example:

        searchNode = 'coordinates'

    """

    # Get the children of the node
    children = child.getchildren()

    # This gets the node names (tags) for all the children of the node, minus the namespace text
    childrenTags = [child.tag.split('}')[1] for child in children ]

    # If the number of children is greater than one then it is not what we are
    # looking for, because the <coordinates> node does not have children
    if len( children ) >= 1 :

        # empty list to hold coords
        coords = [ ]

        # Loop through each child for the children
        for child in children:

            # This variable holds the results
            result = get_coords( child, searchNode )

            # Extend the results to the list. You have to do this because if
            # you don't extend it, the list gets overwritten each time so at
            # the end when the recursion bubbles back up the stack it would
            # otherwise write over the results we wanted with an empty list
            coords.extend( result )

        # Return the result so we can continue to process
        return coords

    # If the number of children is '0' and the node matches our search node
    # then we have found the node we want
    elif len( children ) == 0 and child.tag.split('}')[1] == searchNode:

        # return the text inside the node
        return [child.text]
        
    # if it is not what we want then return an empty list
    else:

        return []



def get_kml_data( et, ns, wants, geomType, point_text, polygon_text ):

    # Get the document name and find all the placemarks
    docName, Placemarks = get_doc_name_placemarks( et, ns )

    print
    print '*'*10,' Extracting placemark points in',docName[0],'.kml','*'*10
    print

    # A list to hold the data associated with the point placemarks
    bundle = []
    
    superCoordList = []

    # A list to check for duplicatees
    dupCheck = []

    print 'Extracting point placemark information'

    # For each placemark
    for place in Placemarks:

        if geomType == point_text:

            # temporary holder for coordinates
            tempCoords = []

        elif geomType == polygon_text:

            tempTracker = []

            superCoordListName = []

            # container to hold attribute header data
            attrHead = []

        # temporary holder for attribute row data
        tempRowDat = []
        
        # Get the children of the placemarks
        children = place.getchildren()

        # A container that holds attribute tag data with namespace data removed
        cleanChildren = [ child.tag.split('}')[1] for child in children ]

        # This is to check and make sure that we are only getting
        # coordinates that are associated with 'Points' and NOT polygons or
        # polylines. If 'Point' not in the container then pass it up.
        if geomType not in cleanChildren:

            continue 

        # This code says that if the name was not filled in in Google Earth
        # then throw and error.  This is here becuase it would be hard for
        # data managers to deal with locations that do not have a name
        if wants[0] not in cleanChildren:

            print 'System Exit.  There is a placemark with no name.  Every placemark has to have a name'
            sys.exit(1)

        # Loop through children nodes of placemark
        for child in children:

            # if the tag (minus name space information) is in the 'wants'
            # container then continue 
            if child.tag.split('}')[1] in wants:

                # Get child tag (minus namespace data)
                child_tag = child.tag.split('}')[1]

                if geomType == point_text:

                    # If the 'child_tag' is not equal to 'Point', which means
                    # it is not the coordinate data and we want to grab it
                    if child_tag != point_text:

                        # Append it to the temporary containers
                        tempRowDat.append( child.text )

                        if child_tag == wants[0]:

                            dupCheck.append( child.text )

                    # if it is the 'Point' node, then
                    elif child_tag == point_text:

                        # The search word that will be passed into the
                        # recursion function 'get_coords()
                        searchNode = 'coordinates'
                        
                        # variable holding the results of the 'get_coords()
                        # function (located at the top of this file).  This is
                        # a recursion function that drills down a tree
                        # structure and gets the coordinates for each placemark
                        coords = get_coords( child, searchNode)[0].strip().replace(',0','')
 
                        # Assign the latitude and longitude coordinates
                        lat, long = coords.split(',')

                        # Append to the temporary coordinate holder
                        tempCoords.append( lat.strip() )
                        tempCoords.append( long.strip() )

                elif geomType == polygon_text:

                    # If the 'child_tag' is not equal to 'Point', which means
                    # it is not the coordinate data and we want to grab it
                    if child_tag != geomType and child_tag != wants[0]:

                        # Append it to the temporary containers
                        attrHead.append( child_tag )
                        tempRowDat.append( child.text )

                    elif child_tag == wants[0]:

                        attrHead.append( child_tag )
                        tempRowDat.append( child.text )
                        dupCheck.append( child.text )
                        
                    # if it is the 'Point' node, then
                    elif child_tag == geomType:

                        # The search word that will be passed into the recursion function 'get_coords()
                        searchNode = 'coordinates'
                        
                        # Get the returned value from the recursive method
                        # 'get_coords()'.  We are also stripping off alot of the
                        # extra text and splitting the text into a list
                        coords = get_coords( child, searchNode)[0].strip().replace(',0','').split(' ')

                        # Further manipulating the coords list so that we can use it
                        coords = [ coord.split(',') for coord in coords ]

                        # This puts in boiler plate text if the description was
                        # not filled in in Google Earth
                        while len(tempRowDat) < len(wants[:-1]):

                            tempRowDat.append('Info not supplied in Google Earth')

                        # Package up all the information for a single polygon
                        superCoordList = [ [ docName ] + [  wants[:-1] ] + [ [ tempRowDat ] + coords ] ]
                        
                        # Append that to a list that is holding all the polygons
                        bundle.append( superCoordList )

            # If node is not in the 'wants' container the pass it up
            else:

                pass

            if geomType == point_text:

                # Build a list combining the temporary coordinate and attribute row data
                CoordRowList =  tempCoords + tempRowDat 

        if geomType == point_text:

            # This ensures that for every attribute header there is a row cell
            # value.  If in Google Earth the user didn't enter a 'description'
            # or 'name' value then these wouldn't match up and the ArcGIS would
            # blow up.  This ensures that there is a row cell value for every
            # attribute header value.
            while len( CoordRowList ) < len( wants[:-1] ) + 2:

                CoordRowList.append('Info not supplied in Google Earth')

            # Put together the coordinates list
            superCoordList.append( CoordRowList )
       

        removeDups = list( set(dupCheck) )

        # This is to make sure that every text in the name node is unique.  We
        # want every name to be unique so it doesn't cause us issues later in
        # the project life cycle.  This is a business decision rather than a
        # logic decision, meaning that my script will make sure that every name
        # is unique (which ArcGIS requires), we just want the user to get
        # appropriate names. We also don't want any names that have the default
        # name provided by Google Earth.
        if len( dupCheck ) != len( removeDups ):
            print
            print 'System exit. More than one %s have the same name.' % geomType.lower()
            print 'Go back to Google Earth and make sure that every %s has a unique name.' % geomType.lower()

            sys.exit(1)

        elif 'Untitled Polygon' in removeDups or 'Untitled Placemark' in removeDups:
            print
            print "System exit. There is a %s titled 'Untitled %s'." % ( geomType.lower(), geomType )
            print "Go back to Google Earth and make sure that every point placemark or polygon has a unique name. Also make sure every point or polygon does not have the default name provided by Google Earth."

            sys.exit(1)

    if geomType == polygon_text:

        # Add the geometry type to the bundle. This will be used to diret the logic later on
        bundle = [ geomType ] + bundle

        return bundle
            
    elif geomType == point_text:

        # Build a list holding all the lists to pass it along to the next method
        bundle = [ [ docName ] + [ wants[:-1] ] + [ superCoordList ] ]

        # Add the geometry type to the bundle.  This will be used later on to direct the logic
        bundle = [ geomType ] + bundle

        return bundle

    

class Kml_To_Shapefile:


    def __init__( self, pathToShapeFile, outFolder, coordsys, metadataDict ):

        self.pathToShapeFile = pathToShapeFile
        self.outFolder = outFolder
        self.coordsys = coordsys
        self.metadataDict = metadataDict
        self.geomTracker = []
        self.polygon_text = 'Polygon'
        self.point_text = 'Point'

        # We are only extracting data from these nodes.
        self.wants = [ 'name','description' ]

        # Parse the file
        et = etree.parse( pathToShapeFile )

        # The name space. This has to be used to parse the kml if it was made
        # in Google Earth, where kmls are given namespaces
        ns = 'http://www.opengis.net/kml/2.2'

        # A container that is used to hold the geometry types that are found in
        # a kml, i.e. line, polygon, and/or point
        self.geomTypes = []

        # See if there are points in the kml. If so add it to 'geomTypes' container
        try:

            # check to see if the kml is has 'points'
            geom_checker( et, ns, self.geomTypes, self.point_text )

        # error catcher. If there was none it would blow up without this
        except AttributeError:

            # no need to do anything special here
            pass

        # See if there are polygons in the kml. If so add it to 'geomTypes' container
        try:

            # check to see if the kml is has 'polygons'
            geom_checker( et, ns, self.geomTypes, self.polygon_text )

        # error catcher. If there was none it would blow up without this
        except AttributeError:

            # no need to do anything special here
            pass

        # A loop to execute the proper methods that correspond with ESRI
        # shapefiles.  This is needed because unlike kml files a point and
        # polygon, for instance, can not be in the same shapefile. They would
        # need a shapefile for each geometry type.  This executes the proper
        # method for each geometry type.
        for type in self.geomTypes:

            # If 'Point' is in 'geomType. then execute the '__point' method
            if type == self.point_text:

                self.wants.append( self.point_text )

                self.__point( et, ns, self.point_text )

            # If 'Polygon' is in 'geomType. then execute the '__polygon' method
            elif type == self.polygon_text:

                self.wants.append( self.polygon_text )

                self.__polygon( et,ns, self.polygon_text )


    def __point( self, et, ns, geomType ):

        self.bundle = get_kml_data( et, ns, self.wants, geomType, self.point_text, self.polygon_text )

        self.__prepare_and_sanatize()


    def __polygon(self, et, ns, geomType ):

        
        self.bundle = get_kml_data( et, ns, self.wants, geomType, self.point_text, self.polygon_text)
    
        self.__prepare_and_sanatize()


    def __prepare_and_sanatize( self ):
        
        """
        Unpackage bundle properly to give to the 'IllegalCharsKml' method so
        it will not blow up when we build a shapefile in Esri ArcGIS.
        """

        # Get the geometry type. This will be used to direct the logic
        geomType = self.bundle[0]

        # Delete it or else it will blow up
        del self.bundle[0]

        # If geomType is 'point' then clean it up and send it to the the method
        # that will make arcGIS point shape files
        if geomType == 'Point':

            docName, superCoordList, attrHead, self.point_appending = package_for_make_shapefile( self.bundle, geomType )

            # Repackage the lists to send to ArcGIS
            self.bundle = [ [ docName ] + [ attrHead ] + [ superCoordList ] ]

            # Call the appropriate method
            self.__make_shapefile_point()

            
        elif geomType == 'Polygon':

            # A list that is used to hold all the polygons in the kml.  
            self.superBundle = []

            # for each polygon 
            for poly in self.bundle:

                docName, superCoordList, attrHead, self.poly_appending = package_for_make_shapefile( poly, geomType )
            
                # Repackage the lists to send to ArcGIS
                self.superBundle.append( superCoordList ) 

            # Package it up so it cn be sent to ArcGIS and be processed. It HAS
            # to be packages like this.
            self.superBundle = [ [docName] + [attrHead] + [self.superBundle] ]

            self.__make_shapefile_polygon()


    def __make_shapefile_point( self ):

        """
        Inovkes function to generate point shapefile
        """

        # This is a method located in shapefile.database_to_shapefile_points. It makes the Esri point shapefile
        self.outFile = make_shapefile_point_esri_v9( self.bundle, self.outFolder, self.coordsys )

        # Appending only non-duplicate geometry types. This will be used in the zip_it() method if need be.
        if self.point_appending not in self.geomTracker:

            self.geomTracker.append( self.point_appending )

        self.__make_metadata()

    def __make_shapefile_polygon( self ):

        """
        Inovkes function to generate polygon shapefile
        """

        # This is a method located in shapefile.database_to_shapefile_points. It makes the Esri point shapefile
        self.outFile = make_shapefile_polygon_esri_v9( self.superBundle, self.outFolder, self.coordsys )

        # Appending only non-duplicate geometry types. This will be used in the zip_it() method if need be.
        if self.poly_appending not in self.geomTracker:

            self.geomTracker.append( self.poly_appending )

        self.__make_metadata()


    def __make_metadata( self ):

        """
        Wraps function into method to write shapefile metadata
        """

        xmlFilePath = os.path.join( self.outFolder, self.outFile + '.xml')

        make_shapefile_metadata( xmlFilePath, self.metadataDict )


    def putBackLegals( self, outFolder, putBack=None ):

        if putBack == None:
            pass

        else:

            putBackLegals( outFolder, putBack )

        





