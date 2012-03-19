import os, pdb


def write_placemark( file_obj, place_mark_name, coords_kml, bubbledata, bubbleFields, geom_type ):

    """
    General function that creates the placemark tag.  This works for polylines, polygons and points.
    """

    # Write opening placemark tag and name.  All geom_types share this
    file_obj.write(
                    '<Placemark>\n'
                    '<name> %s </name>\n' % place_mark_name +
                    '<description>\n'
                  )


    index_sync = 0

    # Writing the desription node, syncronizing the attribute column
    # names with the atttribute column row data
    for data in bubbledata:

        # Writing html 
        file_obj.write('<p> <b> %s: </b> %s </p>\n' % ( bubbleFields[ index_sync ], data ))

        # add one to the counter
        index_sync += 1


    # If it is a point then write the appropriate tags for coordinates and ending placemark tag
    if geom_type == 'Point':
        
        # Close the desription tag and write out the coordinates
        file_obj.write(
                        '</description>\n'
                        '<Point>\n'
                        '<coordinates> %s, %s </coordinates>\n' % ( coords_kml[0], coords_kml[1] ) +
                        '</Point>\n'
                        '</Placemark>\n'
                      )


    # If it is a polyline then write the appropriate tags for coordinates and ending placemark tag
    elif geom_type == 'Polyline':

        # Write the closing description tag and opening coordinate tag
        file_obj.write(
                        '</description>'
                        '<styleUrl>#msn_ylw-pushpin</styleUrl>\n'
                        '<LineString>\n'
                        '<tessellate>1</tessellate>\n'
                        '<coordinates>%s' % coords_kml + '\n'
                        '</coordinates>\n'
                        '</LineString>\n'
                        '</Placemark>\n'
                      )

    # If it is a polygon then write the appropriate tags for coordinates and ending placemark tag
    elif geom_type == 'Polygon':

        # Write the closing description tag and opening coordinate tag
        file_obj.write(
                        '</description>\n'
                        '<Polygon>\n'
                        '<tesselate>1</tesselate>\n'
                        '<outerBoundaryIs>\n'
                        '<LinearRing>\n'
                        '<coordinates> %s </coordinates>' % coords_kml +'\n'
                        '</LinearRing>\n'
                        '</outerBoundaryIs>\n'
                        '</Polygon>\n'
                        '</Placemark>\n'
                      )



def make_kml( outFolderKml, kmlFileName, coordFileToList, geom_type, bubbleFields=None, **kwargs ):

    """
    Summary: Makes a kml file.  This is used in the csvToKml class and
    shapefileToKml class. Writes the kml to file. 

    'outFolderKml' - path to where the kml will be saved. For example:

        C:\\To\Some\directory

    'kmlFileName' - the name of the kml. For example:

        myKmlName.kml
    
    'bubbleFields' - A list of items that were the header column names, minus
    the latitude, longitude, name. For example,
        
        ['Id','name','description']

    'coordFileToList' - Nested lists of coordinates and row data. For example:

        [
          [[-81.2345,'31.22345'],['-81.45634','31.24355',['-81.32523','31.452'],['id_1','Tupelo','some description]],
          [[-81.4345,'31.92345'],['-81.731.24355',['-81.52523','31.452'],['id_2','some name','some description]],
        ]

    'kwargs' -  
        
        'fromShapfile=True' - a keyword argument that directs the logic if the
        kml is being generated from a shapefile. For example:
            
            fromShapefile=True

        'UniqueLines=aList' - a keyword argument at has to be used if the kml
        is being generated from a csv file. The 'aList' is a list of unique
        features (i.e.  polygons). For example:
            
            aList = ['Sapelo','Ogeechee','St.Mary']
            UniqueLines=aList

    """

    # Outpath to where the kml is saved
    kmlOutFolderPath = os.path.join( outFolderKml, kmlFileName)

    print 'Creating KML: ', kmlFileName
    print 'Saving KML to: ', kmlOutFolderPath 
    
    # Open file for writing
    file_obj = open( kmlOutFolderPath , 'w' )

    # write to file. NOTE: all features are white because this is a generic xml header, that 
    # doesn't actually conform to Google Earth standards.  The features are white because
    # that is the default in Google Earth for mal formed kmls.
    file_obj.write('<?xml version="1.0" encoding="UTF-8"?>\n'
        '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
        '<Document>\n'
        '<name>%s</name>\n' % kmlFileName +
        '<StyleMap id="msn_shaded_dot">\n'
        '<Pair>\n'
        '<key>normal</key>\n'
        '<styleUrl>#sn_shaded_dot</styleUrl>\n'
        '</Pair>\n'
        '<Pair>\n'
        '<key>highlight</key>\n'
        '<styleUrl>#sh_shaded_dot</styleUrl>\n'
        '</Pair>\n'
        '</StyleMap>\n'
        '<Style id="sh_shaded_dot">\n'
        '<IconStyle>\n'
        '<color>ff00ffaa</color>\n'
        '<scale>0.945455</scale>\n'
        '<Icon>\n'
        '<href>http://maps.google.com/mapfiles/kml/shapes/shaded_dot.png</href>\n'
        '</Icon>\n'
        '</IconStyle>\n'
        '<ListStyle>\n'
        '</ListStyle>\n'
        '</Style>\n'
        '<Style id="sn_shaded_dot">\n'
        '<IconStyle>\n'
        '<color>ff00ffaa</color>\n'
        '<scale>0.8</scale>\n'
        '<Icon>\n'
        '<href>http://maps.google.com/mapfiles/kml/shapes/shaded_dot.png</href>\n'
        '</Icon>\n'
        '</IconStyle>\n'
        '<ListStyle>\n'
        '</ListStyle>\n'
        '</Style>\n'
        )


    # Checks to see if the data is coming from a parsed shapefile 
    if kwargs.has_key('fromShapefile') and kwargs['fromShapefile'] == True:

        # A counter used to name the polygons and to synchronize the identifier
        # that ArcGIS uses (so you can compare the kml and the shapefile).
        FIDCounter = 0

        # for each polygon in the shapefile
        for coord in coordFileToList: 

            # Checks to see if it was a polygon shapefile
            if geom_type == 'Polygon':

                # Build coordinates
                coords_kml = [ ',0 '.join(','.join( str(x) for x in nlst) for nlst in coord[:-1] ) ][0] + ',0'
                
                # Write placemark tag for placemark
                write_placemark( 
                                 file_obj, 
                                 FIDCounter,     # place_mark_name
                                 coords_kml,     # coordinates 
                                 coord[-1:][0],  # bubbledata 
                                 bubbleFields,   # bubbleFields
                                 geom_type
                                )

            # Checks to see if it was a point shapefile
            elif geom_type == 'Point':

                # Write placemark tag for placemark
                write_placemark( 
                                file_obj, 
                                FIDCounter,                 # place_mark_name
                                [ coord[0], coord[1] ],     # coordinates [ lat, long ] 
                                coord[2:],                  # bubbledata 
                                bubbleFields,               # bubbleFields
                                geom_type
                               )

            # add one to the counter
            FIDCounter += 1


    # Checks to see if the data is coming from a parsed csv file
    elif kwargs.has_key('parsed_csv'):

        # Checks to see if it was a csv file for points
        if geom_type == 'Point': 

            # for each list(coord) we are going to write it to the pop up bubble in
            # Google Earth. This is what appears when you click on a placemark a
            # bubble opens up.
            for coord in coordFileToList: 

                # Write placemark tag 
                write_placemark( 
                                file_obj, 
                                coord[0],                             # place_mark_name
                                [ coord[-2:][0], coord[-1:][0] ],     # coordinates [ lat, long ]
                                coord,                                # bubbledata
                                bubbleFields,                         # bubbleFieds
                                geom_type
                               )


        # Checks to see if it was a csv file for polylines of polygons.  These two share a
        # significant portion of logic to generate both
        elif geom_type == 'Polygon' or geom_type == 'Polyline':

            unique_features = kwargs['parsed_csv']

            # List that holds all the information related to a polyline, a list of lists
            unique_feature_list = []

            # For each in the unique list of polylines 
            for feature in unique_features:

                # for each list in the every row of the csv file
                for coord in coordFileToList:

                    # if each is the same as coord[0], which is the index where the
                    # polyline name is located.
                    if feature in coord[0]:

                        # if they are equal to each other append it to unique_feature_list
                        unique_feature_list.append(coord)

            
                if geom_type == 'Polyline': 
                   
                    # Build coordinates
                    coords_kml = [ ',0 '.join( ','.join(coords[-2:]) for coords in unique_feature_list ) ][0]

                elif geom_type == 'Polygon':

                    # Build the coordinates
                    coords_kml = [ ',0 '.join( ','.join(coords[-2:]) for coords in unique_feature_list ) ][0] + ',0 ' + ','.join(unique_feature_list[0][-2:]) + ',0 '
                
                # Write placemark tag 
                write_placemark( 
                                file_obj, 
                                feature,                      # place_mark_name
                                coords_kml,                   # coordinates 
                                unique_feature_list[0][:-2],  # bubbledata minus lat and long coords
                                bubbleFields[:-2],            # bubbleFieds minus lat and long headers
                                geom_type
                               )

                # make the unique_feature_list list empty for the next polyline
                unique_feature_list = []


    # Close document tags
    file_obj.write('</Document>\n'
            '</kml>')
    # close file
    file_obj.close()    
    
    print 'Kml complete'
    print ''
   
