import os, sys, re, os, zipfile, glob, shutil, csv, itertools, pdb
from pygis.shapefile.metadata import Write_Metadata, make_shapefile_metadata
from numpy import *

# The arcgisscripting and pyodbc are imported only in the functions that require them so that 
# a user can use the functionalities of the library that only require libraries that are shipped 
# with python 2.5

def connect_and_query_database( databaseCnxnInfo, sql ):

    """
    Generic database connection and database query function that (will)
    be used for every database connection and query for entire library
    """

    # Adding import statement here rather than at top so that a user can use the functionalities
    # that don't require outside and supplmental libraries
    import pyodbc

    # Database connection info
    cnxn = pyodbc.connect( databaseCnxnInfo )

    # Create a cursor
    cursor = cnxn.cursor()

    # execute sql command 
    cursor.execute( sql )

    # close database connection
    cnxn.close

    # Return all results from query
    return cursor.fetchall()



def query_database_distinct_shapefiles( databaseCnxnInfo, distCol, databaseTable ):

    """
    Summary: This method querys the database and returns a list of distinct/unique
    values.  Specifically, this method is used in the shapefile classes to get
    a distinct list of shapefiles.

    'databaseCnxnInfo' -  See http://code.google.com/p/pyodbc/wiki/GettingStarted for 
    more database connection information and options.  It should be something like:
        
        databaseCnxnInfo = 'DSN=???????;UID=???????;PWD=??????'

    'distCol' - Column name that holds the rows that shapefiles will be created for and named after
    It should be something like:
        
        shapefileColumnName = 'Accession'

    'databaseTable' - Database table name you are retreiving data from. It should be something like:
    
            databaseTable = 'dbo.somedatatable'

    """

    import pyodbc

    sql = """
           select distinct(%s)
           from %s """ % ( distCol, databaseTable )

    # Assign variable results of sql query
    rows = connect_and_query_database( databaseCnxnInfo, sql )

    # Geting on the return shapefile names
    shapefileName = [ row[0] for row in rows ]  
    
    # Have to return a value
    return shapefileName 


def query_database_indv_shapefile_data( databaseCnxnInfo, distCol,
                        databaseTable, pointDeciderColumn,
                        queryingColumns, Lat, Long, site ):

    """
    Summary: This method querys the database and returns data for the arguments
    passed in.  Specifically, this method is used in the shapefile classes to get
    data about a specific shapefile.

    'databaseCnxnInfo' -  See http://code.google.com/p/pyodbc/wiki/GettingStarted for 
    more database connection information and options.  It should be something like:
        
        databaseCnxnInfo = 'DSN=???????;UID=???????;PWD=??????'

    'distCol' - Column name that holds the rows that shapefiles will be created for and named after
    It should be something like:
        
        shapefileColumnName = 'Accession'

    'databaseTable' - Database table name you are retreiving data from. It should be something like:
    
            databaseTable = 'dbo.somedatatable'

    'pointDeciderColumn' - Column name from the database table/view (in a list and in single quotes. ONLY ONE ITEM
    IS ALLOWED IN THIS LIST) . For each shapefile (as determined in 'Question 5'), a polygon
    will be created for each distinct row in this database table/view column. For LTER GCE
    purposes this is probably 'SiteCode' or 'Accession'.  This column might
    also be known as a 'polygonDeciderColumn' It should be something like:
    
            polygonDeciderColumn = ['SiteCode']

    'Lat' - The column name in the database that holds the Latitude
    coordinates. It should be someting like:

            Lat = 'Latitude'
    
    'Long' - The column name in the database that holds the Longitude
    coordinates
    
            Long = 'Longitude'

    'site' - Is the the shapefile.  This will most likely be an an item in an
    iterator. For example:

        for site in sites:

            query_database_indv_shapefile_data( args, site)       

    """

    import pyodbc

    # Adding together variables to one list for input into sql query
    querys = pointDeciderColumn + queryingColumns

    # Query list used in sql query
    sqlquerys = ','.join( querys )
   
    sql = """
          select %s,%s,%s, %s 
          from %s 
          where %s IN ('%s')  
          """ % (
                  distCol, 
                  Long, 
                  Lat,
                  sqlquerys, 
                  databaseTable, 
                  distCol, 
                  site
                )

    # Assign variable results of sql query
    rows = connect_and_query_database( databaseCnxnInfo, sql )

    # Convert the returned tuple into a list
    allCoordList = [ list(each) for each in rows]

    # Insert the querys as the first item in the list so it can be passed to
    # the class that is using it.  Most likely the class will unpack the
    # 'query'' variable and delete it.
    allCoordList.insert( 0, querys )

    return allCoordList
    

def make_shapefile_attr_table_columns_esri_v9( gp, firstRow, columnNames, outFile ):

    """
    Summary: This is a method that is used in every function that generates
    ESRI shapefiles using data from a database.  It generates the attribute table column names. It
    genertes appropriate datatypes for the attribute table names based on the
    datatypes it uses from the database. The datatypes supported are: 1)text,
    2) Double, and 3) Long.

    'gp' - This is the ArcGIS ESRI geoprocessor object. It will most likely be
    simply "gp". For example,
            
        gp = gp

    'firstRow' - This is the first row of the data that will be used to
    populate the attribute table name.  This is NOT the attribute table column
    names.  Given the attribute column names are: SiteCode, Hectares,
    Ownership. Then 'firstRow' would be something like:

        firstRow = ['GCE-IC', 2983.567, 'Public']

    'columnNames' - This is the what will be used to populate the attribute
    column names.  Give the exaple above:

        columnNames = ['SiteCode','Hectares','Ownership']

    'outFile' - This is the file that is being operated on.  This is NOT the
    entire path, but only the file name

    """

    # Adding import statement here rather than at top so that a user can use the functionalities
    # that don't require outside and supplmental libraries
    import arcgisscripting

    if len( firstRow ) == len( columnNames ):
        pass

    else:

        del firstRow[:2]

    # a counter to synchronize the adding items in the 'columnNames' list.
    index_sync = 0

    # The following block of code iterates through the copy of the first list item
    # in 'superCoordList.  Depending on the data type, a column will be added with
    # the corresponding data type.  The atribute table columns will be created for
    # each item in 'columnNames'.  The list items  in 'lineCopy' are used to determine
    # the datatype for the corresponding column name (i.e. query).  If the data types
    # are float or integer, then a corresponding column with a data type of 'DOUBLE'
    # or "LONG" will be created. If the data type is not 'float' or 'integer' then
    # create a 'string' column.

    # for each in 'lineCopy'
    for index, row_value in enumerate( firstRow ):

        if isinstance( row_value, float):

            # Then create an attribute table column with the data type 'DOUBLE'
            gp.addfield ( outFile, columnNames[ index_sync ], "DOUBLE", "20","20", "#", "#", "#", "#", "#")

            # add one to index1 (our counter)
            index_sync += 1

            # exit the iteration
            continue

        if isinstance( row_value, int ):

            # Then create an attribute table column with the data type 'LONG'
            gp.addfield ( outFile, columnNames[ index_sync ], "LONG", "20","20", "#", "#", "#", "#", "#")

            # add one to index1 (our counter)
            index_sync += 1

            # exit the iteration
            continue

        # if data type is not 'float' or 'int' then create a 'string' column 
        else:
            
            # Then create an attribute table column with the data type 'TEXT'
            gp.addfield ( outFile, columnNames[ index_sync ], "TEXT", "20","20", "250", "#", "#", "#", "#")

            # add one to index1 (our counter)
            index_sync += 1


def make_shapefile_attr_table_rows_esri_v9( cur, row, firstRow, columnNames ):

    """
    Summary: This is a method that is used in every function that generates
    ESRI shapefiles using data from a database.  It sets the row values for
    the attribute table rows.
    
    
    'cur' - This is the ArcGIS ESRI geoprocessor object. It will most likely be
    simply "cur". For example,
            

    'firstRow' - This is the first row of the data that will be used to
    populate the attribute table name.  This is NOT the attribute table column
    names.  Given the attribute column names are: SiteCode, Hectares,
    Ownership. Then 'firstRow' would be something like:

        firstRow = ['GCE-IC', 2983.567, 'Public']

    'columnNames' - This is the what will be used to populate the attribute
    column names.  Give the exaple above:

        columnNames = ['SiteCode','Hectares','Ownership']

    """

    import arcgisscripting

    # Variable that helps synchronize the indexs for setting data in the attribute table rows
    index_sync = 0

    # for each in line
    for index, row_value in enumerate( firstRow ):

        # Try to set the value.  It will try each data type until it finds a datatype that it is
        # compatible with.
        try:

            # Within this try block, first attempt. This will work for
            # 'float', 'integer', and 'text' data types (i.e. the ones
            # that were added in the 'gp.addfield' code
            try:
                
                # Sets the values to the cooresponding row
                row.SetValue( columnNames[ index_sync ], firstRow[ index_sync ] )
                         
                # Add one to count so we can go to the next index
                index_sync += 1

            # If it can not do the above the try the below
            except:

                # if it is not a 'float', 'integer' , or 'text' data type then convert it to a 'text' data type
                firstRow[ index ] = str( row_value )
                
                # Sets the values to the cooresponding row
                row.SetValue( columnNames[ index_sync ], firstRow[ index_sync ] )
                         
                # Add one to count so we can go to the next index
                index_sync += 1

        # If for some reason the above fails, set the row value to 'null'
        except:

            # Sets the values to the cooresponding row
            row.SetValue( columnNames[ index_sync ], 'null' )
                     
            #Add one to count so we can go to the next index
            index_sync += 1
    

    # ArcGIS Requirement: Step 5: Commit row to attribute table
    cur.InsertRow(row)

def sanitize_header( querys, replace_with, max_length=None ):

    """
    Removes non-permitted characters from querys/attribute table column names

    max_length - optional. Length of querys/attribute table column headers.  Shapefiles only allow a
    length of 10 characters while filegeodatabases allow a length of 64 characters
    """

    if max_length == None:

        max_length = 10

    # Regex to search for non-permited characters in querys
    query_regex = r'[^a-zA-Z0-9_]'

    # Get all non-permitted values for every item in querys
    non_permited = [ re.findall( query_regex, value) for value in querys if re.findall( query_regex, value) != [] ]

    # Dictionary to hold all non-permitted characters and their replacement in found querys
    replace_dict_querys = {}

    # Flatten the nested list of non-permited values and add each to the replace_dict_querys as the key and '__' as the value
    [ replace_dict_querys.update({ value : replace_with }) for value in  list( itertools.chain(*non_permited) ) ]

    # Check for non-permitted values in querys. If one is found then replace it with a '__'
    for index, query in enumerate( querys ):

        querys[index] = ''.join( replace_values(  list( query ), replace_dict_querys ) )

    # Make all querys 10 or less characters. ArcGIS shapefiles attrbute column names are not allowd to be longer than 10 characters
    querys = [ str( value[:max_length] ) if len( str(value) ) > max_length else str( value ) for value in querys ]    

    return querys


def sanitize_filename( filename, replace_with ):

    """
    Removes non-permitted characters from filename
    """

    # find all characters that are not permitted to be in a shapefilename.
    #filename = replace_values_helper( r'[^a-zA-Z0-9_]', filename, replace_with )
    
    #filename = ''.join( filename )

    # regular expression. find all non letter and non number characters
    # in each. if any are found they will be returned in a list 
    illegals = re.findall( r'[^a-zA-Z0-9_]', filename )

    for illegal in illegals:
        filename = filename.replace( illegal, replace_with )

    return filename


def putBackLegals( outFolder, putBack=None ):

    """
    Summary: This method allows you to replace escaped characters that occured
    in the shapefile names.  It allows you to replace all the escaped
    characters with one character, which is an argument passed in.
    
    'outFolder' - The location where the shapefiles were saved to. This should
    be the fully qualified path.
    
    'putBack' - This is an optional argument.  This is a string that will
    replace the escaped characters.

    """

    print 'Replacing escaped characters'    

    if putBack != None:

        os.chdir( outFolder )

        for thefile in os.listdir( os.getcwd() ):

            newthefile = thefile.replace( '__', putBack )
            os.rename( thefile, newthefile)



def get_shapefile_data( shapeFilePath ):

    """
    Summary:  This method opens an ESRI shapefile and extracts all the
    vertices for every feature (point, polygon), attribute table data names and
    attribure table row data.  All this data is packaged in a bundle (a
    list) to pass to a generate kml method.  The method automatically
    detects the geometry type (point or polygon) and passes it to the
    proper 'make kml' method. Both Esri code and Ogr code are used here. It
    will try using Ogr because it is a lot faster, and if that fails then it
    will try ESRI code
    """

    kmlBundle = [ ]
    fileRoot = ''
    geomTracker = ''
    exclude = [ 'FID','Shape', 'Id' ]
    curDir, theFile = os.path.split ( shapeFilePath )

    fileRoot, fileExtension = theFile.split('.')

    # set the working directory
    os.chdir( curDir )

    try:
    
        from osgeo import ogr

        # get the shapefile driver
        driver = ogr.GetDriverByName( 'ESRI Shapefile' )

        # open the data source
        datasource = driver.Open( theFile , 0)

        if datasource is None:
            print 'Could not open file'
            sys.exit(1)

        # get the data layer
        layer = datasource.GetLayer()

        # loop through the features in the layer
        feature = layer.GetNextFeature()

        # Holder for the coordinate and attribute row data
        coordHolder = [ ]

        while feature:

            extent = layer.GetExtent()
            
            # holds attribute column items
            headerHolder = [ ]

            # holds attribute row data, i.e. coordinates and correspoding data to 'headerHolder'
            tempCoordHolder = []
           
            # Gets the geometry type for the shapefile
            geom = feature.GetGeometryRef()

            # Gets attribute information
            feat_defn = layer.GetLayerDefn()

            # If the geometry type is not empty and is a 'point'
            if geom is not None and geom.GetGeometryType() == ogr.wkbPoint:

                # A geometry tracker variable used to direct the logic for
                # calling the proper  method to generate the kml, i.e. whether
                # or not to call 'toPoint' or 'toPolygon'
                geomTracker = 'Point'

                # a temperory container that holds the lat and longs
                tempCoordHolder.extend( [ geom.GetX(), geom.GetY() ] )

                # Loop through all attributes and get data
                for i in range(feat_defn.GetFieldCount()):

                    if feature.GetFieldDefnRef(i).GetName() in exclude:
                        continue

                    # used to access attribute columns
                    field_defn = feat_defn.GetFieldDefn(i)

                    # Add to 'headerHolder' list
                    headerHolder.append( feature.GetFieldDefnRef(i).GetName() )

                    # Add attribute row data to temporary list
                    tempCoordHolder.append( feature.GetField(i) )

            # If the geometry type is not empty and is a 'polygon'
            elif geom is not None and geom.GetGeometryType() == ogr.wkbPolygon:

                # A geometry tracker variable used to direct the logic for
                # calling the proper  method to generate the kml, i.e. whether
                # or not to call 'toPoint' or 'toPolygon'
                geomTracker = 'Polygon' 

                # Get the outer ring object
                ring = geom.GetGeometryRef(0)

                # number of points in outer ring
                points = ring.GetPointCount()    

                # for every vertices in points
                for p in xrange( points ): 

                    # Get the lat, long, and z value
                    lon, lat, z = ring.GetPoint( p )

                    # Add them to tempeorary list
                    tempCoordHolder.append( [ lon, lat ] )

                # holder for attribute row data
                attrRowHolder = []

                # Loop through all attributes and get data
                for i in range(feat_defn.GetFieldCount()):

                    if feature.GetFieldDefnRef(i).GetName() in exclude:
                        continue

                    # used to access attribute columns
                    field_defn = feat_defn.GetFieldDefn(i)

                    # add attribute columns to 'headerHolder'
                    headerHolder.append(  feature.GetFieldDefnRef(i).GetName()  )

                    # Add vertices and attribure row data to list
                    attrRowHolder.append( feature.GetField(i) )

                # Add all the related vertices and attribute row data for the
                # feature in the polygon to the 'tempCoordHolder'
                tempCoordHolder.append( attrRowHolder )

            # If the geometry is not a 'point' or 'polygon' then print message and exit
            else:

                print 'Could not processe file. this script can only process point and polygon shapefiles'
                sys.exit(1)


            # Append 'tempCoordHolder' to coordHolder
            coordHolder.append( tempCoordHolder )

            # destroy the feature and get a new one
            feature.Destroy()

            # Go to the next feature in the shapefile
            feature = layer.GetNextFeature()

        # close the data source 
        datasource.Destroy()


    # If OGER is not installed then use ArcGIS
    except ImportError:

        import arcgisscripting

        # Create the geoprocessor object
        gp = arcgisscripting.create(9.3)

        # Identify the geometry field
        desc = gp.Describe( shapeFilePath )
        shapefieldname = desc.ShapeFieldName

        # Get the spatial reference
        spatial_reference = desc.SpatialReference.Name

        # Create search cursor
        rows = gp.SearchCursor( shapeFilePath )
        row = rows.Next()

        # Holder for the coordinate and attribute row data
        coordHolder = [ ]

        # Enter while loop for each feature/row
        while row:

            # holds attribute column items
            headerHolder = [ ]

            # holds attribute row data, i.e. coordinates and correspoding data to 'headerHolder'
            tempCoordHolder = []

            # Create the geometry object
            feat = row.GetValue(shapefieldname)

            # Get Geometry Type
            geometry_Type = feat.Type

            # Get the area of the feature
            geometry_Area = feat.Area

            # Get the centroid for the feature
            geometry_Centroid = feat.Centroid

            # Get the extent for the feature
            geometry_Extent = feat.Extent

            if geometry_Type == 'polygon':

                # A geometry tracker variable used to direct the logic for
                # calling the proper  method to generate the kml, i.e. whether
                # or not to call 'toPoint' or 'toPolygon'
                geomTracker = 'Polygon' 

                # Variable to keep track of how many multipart polygons are in featureclass
                partnum = 0 

                # Count the number of points in the current multipart feature
                partcount = feat.PartCount

                # Enter while loop for each part in the feature (if a singlepart feature
                # this will occur only once)
                while partnum < partcount:

                    # Print the part number
                    part = feat.GetPart(partnum)
                    pnt = part.Next()
                    
                    pntcount = 0

                    # Enter while loop for each vertex
                    while pnt:

                        # Add them to tempeorary list
                        tempCoordHolder.append( [ pnt.x, pnt.y ] )

                        pnt = part.Next()

                        pntcount += 1

                        # If pnt is null, either the part is finished or there is an interior ring
                        if not pnt:
                            pnt = part.Next()
                            if pnt:
                                pass

                    partnum += 1

                # holder for attribute row data
                attrRowHolder = []

                # Get all the fields for the feature class
                fields = desc.Fields

                total_number_of_fields = len( fields )

                field_num_cntr = 0

                # Loop through all the fields in the feature class
                for field in fields:

                    # Take out these default field names
                    if field.Name in exclude :
                        continue

                    else:
                        pass

                    # Add to 'headerHolder' list
                    headerHolder.append( str(field.Name) )
                    
                    # If it is a unicode convert it to a string
                    if isinstance( row.GetValue( field.Name ), basestring ) == True:

                        # Add attribute row data to temporary list
                        attrRowHolder.append( str( row.GetValue( field.Name ))  )
                        
                    else:
                        # Add attribute row data to temporary list
                        attrRowHolder.append(  row.GetValue( field.Name )  )

                    field_num_cntr += 1


                # Add all the related vertices and attribute row data for the
                # feature in the polygon to the 'tempCoordHolder'
                tempCoordHolder.append( attrRowHolder )

            elif geometry_Type == 'point':

                # A geometry tracker variable used to direct the logic for
                # calling the proper  method to generate the kml, i.e. whether
                # or not to call 'toPoint' or 'toPolygon'
                geomTracker = 'Point'

                # Get all the fields for the feature class
                fields = desc.Fields

                total_number_of_fields = len( fields )

                field_num_cntr = 0

                # Loop through all the fields in the feature class
                for field in fields:

                    # Take out these default field names
                    if field.Name in exclude:
                        continue

                    # If it is a unicode convert it to a string
                    if isinstance( row.GetValue( field.Name ), basestring ) == True:

                        # Add attribute row data to temporary list
                        tempCoordHolder.append( str( row.GetValue( field.Name ) )  )
                    else:
                    
                        # Add attribute row data to temporary list
                        tempCoordHolder.append(  row.GetValue( field.Name )  )

                    # Add to 'headerHolder' list
                    headerHolder.append( str(field.Name) )

                    field_num_cntr += 1

                feat = row.GetValue(shapefieldname)

                # Get coords
                pnt = feat.GetPart()

                # a temperory container that holds the lat and longs
                tempCoordHolder.insert( 0,  pnt.y )
                tempCoordHolder.insert( 0,  pnt.x )

            # Append 'tempCoordHolder' to coordHolder
            coordHolder.append( tempCoordHolder )

            row = rows.Next()

    # Make a bundle holding all the shapefile's data to pass to the proper
    # make kml method
    kmlBundle = [ headerHolder ] + coordHolder

    return kmlBundle, headerHolder, coordHolder, geomTracker, fileRoot


def create_file_and_projection_esri_v9( shp_fc_name, outFolder, coordsys, geomType, **kwargs ):

    import arcgisscripting

    #ArcGIS Requirement
    gp = arcgisscripting.create(9.3)
    gp.Overwriteoutput = 1

    # ArcGIS Requirement: Sets the workspace
    gp.workspace = outFolder

    # If a 'fileGDB' kwarg was passed in, meaning we are making a file geodatabase and adding featureclasses to the geodatabase
    if kwargs and 'fileGDB' in kwargs:

        # Gets the file geodatabase name
        fileGDBName = kwargs['fileGDB']

        # Adds '.shp' to 'outFile' to make shapefile name
        outFile = '%s' %  shp_fc_name

        print 'Adding featureclass:', outFile, 'to geodatabase: ', fileGDBName

        ######## Creating FeatureClass ###########
        # ArcGIs requirement. Makes the feature class. This is a point feature class
        gp.CreateFeatureClass ( fileGDBName , outFile, geomType, '#', '#', '#', '#')

        # ArcGIs requirement: gp.toolbox is required to assign coordinate system to feature class
        gp.toolbox = "management"

        # This is the path to the feature class. 
        fcPath = os.path.join( outFolder, fileGDBName, outFile ) 
        
        # ArcGIs requirement: defines the projection
        gp.defineprojection( fcPath , coordsys)

        # Sets self.outFile to the 'fcPath' because for the rest of the
        # script to process the fully qualified path will be needed
        outFile = fcPath

    # Make just shapefiles if no 'fileGDB' kwarg was passed in
    else:

        ########### FILE NAME ############
        outFile = '%s.shp' %  shp_fc_name

        # This replaces the '__' with a '-' to display Python shell text during processing.
        # This does not impact the actual shapefile processing
        print
        print '*'*10, 'Creating', geomType, 'shapefile', outFile,'*'*10
        print

        ######## CREATE FEATURE CLASS ##########
        # 'outFolder' is the location the files will be saved to
        # 'ouFile' is the name of the files
        gp.CreateFeatureClass ( outFolder, outFile, geomType, '#', '#', '#', '#')

        # ArcGIS Requirement: gp.toolbox is required to assign coordinate system to feature class
        gp.toolbox = "management"
          
        # ArcGIS Requirement: Defines the projection
        gp.defineprojection( outFile, coordsys )

    return gp, outFile

   
def make_shapefile_point_shape_esri_v9( gp, coords, outFile ):

    # ArcGIS Requirement: Step 1: Create InsertCursor
    cur = gp.InsertCursor( outFile )
    
    # ArcGIS Requirement: Step 2: Create the 'shape'
    point = gp.CreateObject("Point")

    # ArcGIS Requirement: Create a row
    row = cur.NewRow()
            
    # ArcGIS Requirement: Setting the coordinates
    point.x = coords[ 0 ]
    point.y = coords[ 1 ]

    # ArcGIS Requirement: Setting it to a point geometery
    row.shape = point
    
    return cur, row
    

def make_shapefile_point_esri_v9( bundle, outFolder, coordsys, **kwargs ):

    """
    Summary:  This is the method that is used in the entire pygis library
    to create point shapefiles.  This function does the actual making of the
    shapefile in ArcGIS.
    
    
    superCoordListName - This is the name of the shapefile. For example: 

        superCoordListName = ['NUT__GCEM__0210']

    querys - This is a list of items that could have been used in the sql query
    (if queried a database), could be the header names in a csv file.
    Nevertheless, this is what will be used to create the attribute header
    names in ArcGIS.  For example:

        querys = ['SiteCode']
        
    superCoordList - This is a nested list.  It contains the attribute row
    values and point coordinates.  The first two items in the nested list are
    the coordiantes and after that are what will be used to populate the row
    cells in attribute table in ArcGIS. For example:
    
        superCoordList - [[-81.844499999999996, 31.66711111, 'ALT__BASIN'], [-82.670749999999998, 31.935193999999999, 'ALT__BASIN']]

    """

    import arcgisscripting

    # Grab shapefile name from bundle
    superCoordListName = bundle[0][0][0]

    # Grab querys from bundle
    querys = bundle[0][1]

    # Grab the attribute table data from bundle
    superCoordList = bundle[0][2]
   
    # The geomType to be passed 
    geomType = "POINT"

    # Assign variables and invoke function that generates the shapefile or
    # filegeodatabase/featureclasses and assignes the projection
    gp, outFile = create_file_and_projection_esri_v9( superCoordListName, outFolder, coordsys, geomType, **kwargs )
    
    print 'Adding attribute table fields'

    # Makeing a copy of the first item in the list of 'superCoordList'
    # This will be used to determing the data types for the making of the attribute table fields in ArcGIS
    lineCopy = list( superCoordList[0] )

    # Delete the coordinates. They will blow it up if we don't remove them
    del lineCopy[ :2 ]

    # Calling method from module "from pygis.shapefile.shapefile_utilities import genEsriColumns"
    # to generate the ArcGIS attribute columns
    make_shapefile_attr_table_columns_esri_v9( gp, lineCopy, querys, outFile )  
    
    # Variable to keep track in 'Python shell' of how many points were added for each shapefile       
    point_count = 0 

    # for each line in 'coordFileToList'
    for line in superCoordList:

        # Grab the first two items. They are at the beginning because we reversed the line
        coords = line[ :2 ]

        # Delete this line because it will blow up script
        del line[ :2 ]

        # Create the point shape
        cur, row = make_shapefile_point_shape_esri_v9( gp, coords, outFile )

        # Called method from "from pygis.shapefile.shapefile_utilities import genEsriRows"
        # to generate and insert data into ArcGIS attribute rows in the attribute table
        make_shapefile_attr_table_rows_esri_v9( cur, row, line, querys)  

        # Add one to the 'Count' variable. The variable used to keep track in
        # 'Python shell' of how many points were added for each shapefile 
        point_count += 1
               
    # ArgGis requirement: delete cursor and row so you don't lock ArcGIS
    del cur,row

    print point_count,'points added.'
    print outFile,'created.'

    return outFile


def make_shapefile_array_esri_v9( gp, coordList, outFile ):

    # ArcGIS Requirement: create an 'Array' object
    PolygonArray = gp.CreateObject("Array")
    
    # ArcGIS Requirement: Create the 'Point' object to hold the points
    point = gp.CreateObject("Point")

    # ArcGIS Requirement: Step 1: Create InsertCursor
    cur = gp.InsertCursor( outFile)
    
    # ArcGIS Requirement: Step 2: Create a row
    row = cur.NewRow() 

    ############### ADDING VERTICIES (i.e. COORDINATES) ###################
    # Loop through each coordinate pair in 'coordList'. For each
    # coordinate pair assign the 'point.x' and 'point.y'. Then add the
    # point to the 'PolygonArray'

    for coordinate in coordList:

        # ArcGIS Requirement
        point.x = coordinate[0]
        point.y = coordinate[1]
        PolygonArray.add( point )
        
    # ArcGIS Requirement: To create a polygon, the first coordinate
    # pair and the last coordinate pair must be the same.  This grabs the first
    # coordinate pair in the 'coordList'.
    point.x = coordList[0][0]
    point.y = coordList[0][1]
    PolygonArray.add( point )

    # ArcGIS Requirement: Step 4. Give the row a shape
    row.shape = PolygonArray

    return cur, row

def make_shapefile_array_line_esri_v9( gp, coordList, outFile ):

    # ArcGIS Requirement: create an 'Array' object
    PolylineArray = gp.CreateObject("Array")
    
    # ArcGIS Requirement: Create the 'Point' object to hold the points
    point = gp.CreateObject("Point")

    # ArcGIS Requirement: Step 1: Create InsertCursor
    cur = gp.InsertCursor( outFile)
    
    # ArcGIS Requirement: Step 2: Create a row
    row = cur.NewRow() 

    ############### ADDING VERTICIES (i.e. COORDINATES) ###################
    # Loop through each coordinate pair in 'coordList'. For each
    # coordinate pair assign the 'point.x' and 'point.y'. Then add the
    # point to the 'PolygonArray'

    for coordinate in coordList:

        # ArcGIS Requirement
        point.x = coordinate[0]
        point.y = coordinate[1]
        PolylineArray.add( point )
        
    # ArcGIS Requirement: Step 4. Give the row a shape
    row.shape = PolylineArray

    return cur, row


def make_shapefile_polygon_esri_v9( bundle, outFolder, coordsys, **kwargs ):

    """
    Summary: Function used to create polygon shapfiles
    for the scripts that do that, except for 'OneShapefile_OnePolygon_Database_Eff' (I need to recode it so that it
    will). This includes the kmlToShapefile, CsvToShapefile, etc.

    This function recieves data formatted like:

    superCoordListName:  ['NUT-GCEM-0206']
    querys:  ['Site-Code','Hectares']
    toGisSuperList:  [[['GCE-AL', 4050.9099999999999], [-81.237936000000005, 31.321467999999999], [-81.294621000000006, 31.323284999999998],
                    [-81.239215000000002, 31.296033999999999], [-81.237936000000005, 31.321467999999999]], [['GCE-DB', 2916.4000000000001],
                    [-81.242953999999997, 31.374181], [-81.271884, 31.381208999999998], [-81.281897999999998, 31.381208999999998],
                    [-81.281897999999998, 31.386907000000001], [-81.287460999999993, 31.391655], [-81.288573999999997, 31.397922999999999],
                     [-81.299700000000001, 31.410648999999999], [-81.301479999999998, 31.415396999999999], [-81.287683000000001, 31.355947],
                     [-81.283677999999995, 31.354237999999999], [-81.261425000000003, 31.340941999999998], [-81.242953999999997, 31.374181]],
                     [['GCE-SP', 5662.6199999999999], [-81.154122000000001, 31.556069999999998], [-81.177480000000003, 31.554587000000001],
                     [-81.214085999999995, 31.559628], [-81.235701000000006, 31.553698000000001], [-81.177480000000003, 31.522566000000001],
                     [-81.154122000000001, 31.516635999999998], [-81.154122000000001, 31.556069999999998]]]
    """

    import arcgisscripting

    # Grab shapefile name from bundle
    superCoordListName = bundle[0][0]

    # Grab querys from bundle
    querys = bundle[0][1]
   
    # Grab the 'toGisSuperList'
    toGisSuperList = bundle[0][2]

    geomType = 'POLYGON'

    # Assign variables and invoke function that generates the shapefile or
    # filegeodatabase/featureclasses and assignes the projection
    gp, outFile = create_file_and_projection_esri_v9( superCoordListName[0], outFolder, coordsys, geomType, **kwargs )

    ############# ADDING FIELDS TO ATTRIBUTE TABLE ############
    # Adding fields to attribute table. For details from ArcGIS on '.addfield' go to:
    # http://webhelp.esri.com/arcgisdesktop/9.3/index.cfm?TopicName=Add_Field_%28Data_Management%29

    # Makeing a copy of the first item in the list of 'superCoordList'
    # This will be used to determing the data types for the making of the
    # attribute table fields in ArcGIS make a copy of the first list in 'superCoordList' to pass into module method
    lineCopy = list( toGisSuperList[ 0 ][ 0 ] )

    # Generate the GIS attribute columns
    make_shapefile_attr_table_columns_esri_v9( gp, lineCopy, querys , outFile )

    polygon_counter = 0

    # This is where the coordinates and row values are set
    for coordList in toGisSuperList:

        # Takes only the attributes associated with each 'SiteCode' and assigns to the variable 'attributeValuesOnly'
        attributeValuesOnly = coordList[0]
        
        # Deletes the attribute list. The is a requirement so that only coordinates are passed to the 'PolygonArray'
        del coordList[0]

        # REPLACING BACK ILLEGAL CHARACTERS
        # back to the orginal state as they were recieved from the database.
        # NOTE: THIS IS WHERE YOU WOULD ADD TO IF THERE WERE MORE ILLEGAL CHARACTERS FOUND
        for index, attribute_value in enumerate( attributeValuesOnly ):

            # Replaces only if possible. Will work for strings and nothing else.
            try:

                attributeValuesOnly[ index ] = attribute_value.replace('__','-')

            # If the above fails, simply add it as it is
            except:

                attributeValuesOnly[ index ] = attribute_value
                 

        # Make point array
        cur, row = make_shapefile_array_esri_v9( gp, coordList, outFile )

        ################ SETTING VALUES TO ATTRIBUTE TABLE #############
        # Sets the row values for the corresponding attribute table field.
        # This calls a method in the "from pygis.shapefile.shapefile_utilities import make_shapefile_attr_table_rows_esri_v9"
        # It sets row values to the corresponding columns in the attribute table
        make_shapefile_attr_table_rows_esri_v9( cur, row, attributeValuesOnly, querys )

        polygon_counter += 1

    '''
    # REPLACING BACK ILLEGAL CHARACTERS
    # Replacing the '__' back to '-' as it was originally retrieved from
    # the database
    outFile = outFile.replace('__','-')
    print outFile, 'created'
    '''
        
    # delete cur and row so you don't lock things up
    del cur,row

    print polygon_counter, 'polygons added.'

    # Return the ouFile location. This will be needed in scripts that call this method.
    return outFile


class File_Geodatabase:

    """
    Summary: This class creates a file geodatabase.

    'fileGDBName' - The name of that you want the file geodatabase to be
    called. You can have an extension of '.gdb' or not.  The script will check
    for it and if not there it will add on.
    
    'outFolder' - This is where you want the file geodatabase to be saved.
    """

    def __init__(self, fileGDBName, outFolder ):

        self.outFolder = outFolder

        # if the extension '.gdb' is not included in the file gdb name then it will add it.
        if '.gdb' in fileGDBName:

            self.fileGDBName = fileGDBName

        else:

            self.fileGDBName = fileGDBName + '.gdb'
        
    
    def make_filegeodatabase(self):

        import arcgisscripting

        #ArcGIs requirements
        gp = arcgisscripting.create(9.3)
        gp.Overwriteoutput = 1

        print 'Creating geodatabase:', self.fileGDBName

        # ArcGIS requirement: Sets the workspace
        gp.workspace = self.outFolder

        # ArcGIS handle to create a file gdb
        gp.CreateFileGDB( self.outFolder, self.fileGDBName ) 


def replace_values_helper( regex, search_text, replace_with ):

    # regular expression. find all non letter and non number characters
    # in each. if any are found they will be returned in a list 
    illegals = re.findall( regex, search_text )

    replace_dict = {}

    # Put all illegals that were found into the dictionary with a default value
    [ replace_dict.update( { illegal : replace_with } ) for illegal in illegals ]

    # Check for non-permitted values in shapefile name. If one is found then replace it with a
    # double underscore. Value returned as a list
    search_text = replace_values(  list( search_text ), replace_dict )

    return search_text



def replace_values( data, replace_dict ):

    """
    Using numpy array to quickly process data and replace values from dictionary
    see: http://stackoverflow.com/questions/3403973/fast-replacement-of-values-in-a-numpy-array 
    """

    data = array( data )
    array_copy = copy( data )

    for key, value in replace_dict.iteritems():

         array_copy[data==key] = value

    return array_copy.tolist()


def make_shapefile_wrapper( databaseCnxnInfo, databaseTable, shapefileColumnName, distCol, IndvQueryShapefileName, pointDeciderColumn,
                            queryingColumns, Lat, Long, coordsys,  outFolder, metadataDict,
                            package_for_makeShapefile, site, make_shapefile, kwargs ): 

    """
    Wrapper that querys data for a specific shapefile, prepares the data, and invokes functions to generate
    the shapefile. This is used in 'query_all_and_selected_and_make()'. The arguments are the same as
    the aforementioned function.
    """

    # assiging the variable 'allCoordList' what is returned from
    # 'query_database_indv_shapefile_data()'. 'queryDatabaseIndv()' is a method in the
    # module 'from pygis.shapefile.shapefile_utilities' that
    # retrieves data specfic to a shapefile
    allCoordList = query_database_indv_shapefile_data( databaseCnxnInfo, distCol, databaseTable, 
                                                       pointDeciderColumn, queryingColumns, Lat, Long, site )

    # Get the 'querys' variable. It was packaged in the 'allCoordList' in the 'query_database_indv_shapefile_data' method
    querys = allCoordList[0]

    # delete the querys variable from 'allCoordList'
    del allCoordList[0]

    # If 'rows_replace' kwargs was passed in replace values using dictionary for the entire csv
    # file (except filename and querys)
    if 'rows_replace' in kwargs:
       
        allCoordList = replace_values( allCoordList, kwargs['rows_replace'] )

    # Assign the bundle what is returned from the function.  This packages up the code 
    bundle = package_for_makeShapefile( allCoordList, querys)

    # If 'suffix' kwargs was passed in then add the 'suffix' to the shapefile name
    if 'suffix' in kwargs: 
        bundle[0][0][0] = bundle[0][0][0] + kwargs['suffix']

    # Replaces any non-permitted characters in file name
    bundle[0][0][0] = sanitize_filename( bundle[0][0][0], '__' )

    # If 'header_replace' kwargs was passed in, then replace the headers with values in the dictionary.
    if 'header_replace' in kwargs:
        bundle[0][1] = replace_values( bundle[0][1], kwargs['header_replace'] )

        # Have to check for non-permitted values and length for alternate querys/headers
        bundle[0][1] = sanitize_header( bundle[0][1], '__' )

    # Have to check for non-permitted values and length for alternate querys/headers if 'header_replace' is not passed in
    bundle[0][1] = sanitize_header( bundle[0][1], '__' )

    # Assigning the returned value from the method 'make_shapefile'. 'make_shapefile' is really
    # a generic variable name pointing to a function.  The function is specific to the class that is
    # invoking it. For example, if the class 'Database_To_Shapefile_Points()' is invoking this function,
    # then 'make_shapefile' is really invoking 'make_shapefile_point_esri_v9()'
    outFile = make_shapefile( bundle, outFolder, coordsys, **kwargs )

    # Currently, there is not code to add metadata to a featureclass in a filegeodatabase. So, if a
    # filegeodatabase was created then do NOT try to make metadata
    if 'fileGDB' not in kwargs:

        # Writes metadata file using data passed in with the dictionary
        make_shapefile_metadata( os.path.join( outFolder, outFile + '.xml'), metadataDict )


def query_all_and_selected_and_make( databaseCnxnInfo, databaseTable,
            shapefileColumnName, distCol, IndvQueryShapefileName, pointDeciderColumn,
            queryingColumns, Lat, Long, coordsys,  outFolder, metadataDict,
            package_for_makeShapefile, make_shapefile, **kwargs ):

    """
    'databaseCnxnInfo' - This is the information needed to connect to the databse.
    See http://code.google.com/p/pyodbc/wiki/GettingStarted for  more database connection information and options
    It should be something like:

        databaseCnxnInfo = 'DSN=??????;UID=????????;PWD=??????'

    'databaseTable' - Database table name you are retreiving data from.  It should be something like:

        databaseTable = 'dbo.somedatatable'

    'shapefileColumnName' - The column name that holds the rows that you want make shapefiles for.It should be something like:

        shapefileColumnName = 'Accession'

    'IndvQueryShapefileName' -  Rows from the database table/view column.  A shapefile will be created for and named
    after 1) each distinct row if the an empty list is passed in. So, if you want to make a shapefile for every 
    distinct row in the database table/view colulmn, then make an empty list, for example: [] ; OR 2) each item  
    in the list if the there are items in the list. So,  If you want shapefiles for only select rows, then put 
    the row  text in a list seperated by commas in single quotes. 

        For every distinct row: 
            []

        For selected rows:
            ['NUT-GCEM-0210','PLT-GCET-0608','PLT-GCET-0802a'] .

    'pointDeciderColumn' - Column name from the database table/view (in a list and in single quotes. ONLY ONE ITEM IS ALLOWED IN THIS LIST) .
    For each shapefile , a point will be created for each  row in this database
    table/view column. For LTER GCE purposes this is probably 'SiteCode'. For example: ['SiteCode']
    pointDeciderColumn = ['TypeCode']

    'queryingColumns' -  Column names from the database table/view that are to be included in the sql query (in a list seperated 
    by commas in single quotes).  This list  will be included in the 'select' sql clause.  Also, an 'attribute table field' 
    (in ArcGIS) will be created for each item in this list.

        For example: ['Location','Descr','SubSite','DateStart']

    'Lat' - The exact spelling of the column name that holds the latitude
    coordinates. For example:

        Lat = 'Latitude'

    'Long' -  The exact spelling of the column name that holds the longitude
    coordinates. For example:

        Long = 'Longitude'


    'coordsys' - Path to the coordinate system you want the shapefiles to be projected in.  It should be something like:

        coordsys = 'C:\\Program Files\\ArcGIS\\Coordinate Systems\\Geographic Coordinate Systems\\World\\WGS 1984.prj'

    'outFolder' - The path to the folder where you want the shapefiles saved to. For example

        outFolder = 'C:\Path\To\folder'

    'metadataDict' -  This is a dictionary that has the values and key pairs for data that you want inserted into the 
    xml metadata files.  The dictionary keys HAVE to make exactly the methods
    in 'Esri_metadata' class in 'pygis.shapefiles.metadata'. For example:

        metadataDict = {
            'abstract': 'This is an abstract that I just added',
            'purpose': 'This is my purpose'
            }
    
    'suffix' - This is an optional argument that allows you to append a suffix to the shapefile
    name. 
        
        suffix='_Point'

    'package_for_makeShapefile' - Function.  This function packages up data for the function that
    actually makes the shapefile.  This is specific for each geometry type (point and polygons)

    'make_shapefile' - Function.  This is the function that generates a shapefile for a specific
    geometry type (i.e. make_shapefile_point_esri_v9 or make_shapefile_polygon_esri_v9). It is passed in with name so
    that we can pass in functions with different names but invoke them using the same way.  'make_shapefile' 
    # is really a generic variable name pointing/wrapping/referring to a function.  The function is specific to the class that is
    # invoking it. For example, if the class 'Database_To_Shapefile_Points()' is invoking this function,
    # then 'make_shapefile' is really invoking 'make_shapefile_point_esri_v9()'

    """

    # if self.IndvQueryShapefileName is empty, which means we are going to generate all shapefiles
    if IndvQueryShapefileName == []:

        # assiging the variable 'shapefile' what is returned from
        # 'query_database_distinct_shapefiles()'. 'queryDatabaseDist()' is a method in the
        # module 'from pygis.shapefile.shapefile_utilities' that
        # returns a list of unique/distinct shapefile names for the entire table
        shapefileName = query_database_distinct_shapefiles( databaseCnxnInfo, distCol, databaseTable )

        # Then loop through all the items that were returned with the sql
        # distince query and execute a specific sql statement for each of those items
        for site in shapefileName:
            
            # Invokes wrapper function that invokes all the functions needed to create the shapefile
            make_shapefile_wrapper( 
                                    databaseCnxnInfo, databaseTable, shapefileColumnName, distCol, 
                                    IndvQueryShapefileName, pointDeciderColumn, queryingColumns, Lat, 
                                    Long, coordsys,  outFolder, metadataDict,
                                    package_for_makeShapefile, site, make_shapefile, kwargs 
                                   )

    # Just generate shapefiles for a select few, i.e. the ones in the list
    else:

        # Loop through each ot the items in self.IndvQueryShapefileName and
        # execute a sql statement for each of the items in the list
        for site in IndvQueryShapefileName:

            # Invokes wrapper function that invokes all the functions needed to create the shapefile
            make_shapefile_wrapper( 
                                    databaseCnxnInfo, databaseTable, shapefileColumnName, distCol, 
                                    IndvQueryShapefileName, pointDeciderColumn, queryingColumns, 
                                    Lat, Long, coordsys,  outFolder, metadataDict, 
                                    package_for_makeShapefile, site, make_shapefile, kwargs 
                                   )


def zip_it( outFolder, **kwargs ):

    """
    Summary: For every shapefile in a folder, this method packages 1) All like
    files associated with a shapefile(5 or so of them) into one .zip archive,
    2) all filgeodatabases into a zip archive of their own, 3) If there are already .zip
    archives in the 'outFolder' directory then they will be left alone.
    For example, every shapefile has 5 files or so associated with it (dbf, prj, shp, shp.xml,shx).
    The basename is constant, but the file extensions are different.  This method takes all shapefiles
    with the same basename and packages them into a zip archive using the
    basename as the zip archive name.

    'outFolder' - The path to the directory where the zipfiles are located. For
    example:

        outFolder = r'C:\UserFiles\Path\To\Folder'


    'kwargs' - 

        'descrip' - This is an optial argument (a string) that allows you to append a string
        to the end of the basename that will be used to name the zip archive. For example:

            if the shapefile's basename is 'ALT-BASIN' and you pass in the
            'descrip' argument as '_Aug_03_2011', then the zip file will be named
            'ALT-BASIN_Aug_03_2011.zip'. If this argument was not included, then the
            zip file would be named 'ALT-BASIN'. For example:
                    
                descrip='_Aug_03_2011'


        'ignore_geometry' - This is an optional argument ( a list ) that allows part of
        the file name to be ignored, and all the files with the same basename
        (minus the the string that was in the 'ignore_geometry' list)
        will be put into one .zip archive, named after the basename. This argument will most likely be
        used only if your are zipping files that resulted from 'Kml_To_Shapefile'
        class where there are 'points','polygons', and possibly 'polylines' in one
        kml that are converted to shapefiles, which in this case '_Point' or
        '_Polygon' string will be appended to the shapefile's
        basename,reflectng the geometry type.  The 'Kml_To_Shapefile' class makes a 
        shapefile for each geometry type (point, polygon, polyline) with a
        common basename, and appends an appropriate ending to the file name, such as
        '_Polygon','_Point','_Line', . If this argument was passed in during
        then, the endings would be ignored and all the files with a common
        basename would be put into a single zip archive.  For example:


            If there are files in the 'outFolder' directory: 
                'shapefile_1_Polygon.dbf'
                'shapefile_1_Polygon.prj'
                'shapefile_1_Polygon.shp'
                'shapefile_1_Polygon.shp.xml'
                'shapefile_1_Polygon.shx'
                'shapefile_1_Point.dbf'
                'shapefile_1_Point.prj'
                'shapefile_1_Point.shp'
                'shapefile_1_Point.shp.xml'
                'shapefile_1_Point.shx'

            The result would be:
                shapefile_1.zip (which would contain the files):
                    'shapefile_1_Polygon.dbf'
                    'shapefile_1_Polygon.prj'
                    'shapefile_1_Polygon.shp'
                    'shapefile_1_Polygon.shp.xml'
                    'shapefile_1_Polygon.shx'
                    'shapefile_1_Point.dbf'
                    'shapefile_1_Point.prj'
                    'shapefile_1_Point.shp'
                    'shapefile_1_Point.shp.xml'
                    'shapefile_1_Point.shx'

    """

    # if descrip argument is present and is not None then decrip variable is an empty string
    # else the dic value for 'descrip' is used
    
    descrip = 'descrip'

    if kwargs.has_key(descrip) and kwargs[descrip] != None:
        descrip = kwargs[descrip] 
    else:

        descrip = ""
    
    print "Zipping files" 

    # change current working directory to 'outFolder'
    os.chdir(outFolder)

    # This will get rid of all duplicates when add files to it
    uniqueShapeFiles = set([])

    for spatial_file in os.listdir( os.getcwd() ):

        # if file is a zip file then don't mess with it
        if spatial_file.endswith('.zip'): 
            pass

        # if the file is a geodatabase
        elif spatial_file.endswith('.gdb'):
            pass
            
        else:

            # add only the root file name to the set
            uniqueShapeFiles.add( spatial_file.split('.')[0] )

    # turn the set into a list. 
    uniqueShapeFiles = list(uniqueShapeFiles)

    # if 'ignore_geometry' argument is passed in 
    ignore_geometry = 'ignore_geometry'

    if kwargs.has_key( ignore_geometry ) and len( kwargs[ ignore_geometry ] ) >= 1:

        # Make variable of the the list
        kml_geometry = kwargs[ ignore_geometry ]

        # Makes a list of the UniqueShapeFiles without their appending that was
        # given to them in the 'Kml_To_Shapefile' class
        kml_geom_removed = [ shp.rsplit('_', 1)[0] for shp in uniqueShapeFiles ]

        # Gets only the duplicates
        duplicates_only = [item for item in set(kml_geom_removed) if kml_geom_removed.count(item) > 1 ]

        # If the length of duplicates is zero it throws up
        if len( duplicates_only ) == 0:

            # for every file in the directory
            for File in os.listdir( os.getcwd()):

                # File with no extension
                File_no_extension = File.split('.')[0]

                # for each geom in the ignore_geometry list
                for geom in kwargs[ ignore_geometry ]:

                    # If the file with no extension is the same as 'geom'
                    if File_no_extension.endswith( geom ):

                        # create the zip file basename.  This is the file
                        # without the appending given by the 'Kml_To_Shapefile' class
                        zip_basename = File_no_extension.replace( geom,'' )

                        # Make the zip file location path
                        zipFileLocation = os.path.join( outFolder, zip_basename + descrip + '.zip')

                        # If a zip file with that names already exists, then don't create another one 
                        if os.path.isfile( zipFileLocation):
                            pass

                        # if it doesn't exist, then make one
                        else:
                            z_kml_ = zipfile.ZipFile( zipFileLocation, 'w')

                        # Write the file to the zip
                        z_kml_.write( File )

                        # remove the file
                        os.remove( File )

            # close the zip file
            z_kml_.close()

        # If the length of duplicates_only is greater > 0 
        else:

            for dup in duplicates_only:

                # Create a zip file location
                zipFileLocation = os.path.join( outFolder, dup + descrip + '.zip')

                # Check if there is already a zip file with this name, if so then
                # don't create another one 
                if os.path.isfile( zipFileLocation ):
                    pass

                # If not, make one
                else:

                    # make the zip file
                    z_kml = zipfile.ZipFile( zipFileLocation, 'w')

                # For each file in the directory
                for File in os.listdir( os.getcwd() ):

                    # Get the file basename
                    File_no_extension = File.split('.')[0]

                    # Remove the appendings given during the 'Kml_To_Shapefile'
                    File_no_kml = File_no_extension.rsplit('_',1)

                    # if the duplicate equals the file basename
                    if dup == File_no_kml[0]:

                        # Double checking that the appending is equal to what was
                        # passed in with the 'kml_geometry'. If true, then it is a
                        # fie we want
                        if File_no_kml[1] in [ l.replace('_','') for l in kml_geometry ]:

                            # Add it to the zipfile object
                            z_kml.write(File)

                            # Then remove the file
                            os.remove(File)

            # close the zip file
            z_kml.close()


        # We have to remove any files we ziped during this process so that
        # we don't duplicate a zip file  later on in this script
        for dup in duplicates_only:

            for geom in kml_geometry:

                forRemove = dup + geom

                uniqueShapeFiles.remove( forRemove )


    # If 'ignore_geometry' was not passed in
    else:

        pass
    
    # Loop through each uniqueShapeFile to get all the files related to a specific shapefile
    for uniqueShapeFile in uniqueShapeFiles:

        # Zip file location for each uniqueShapeFile
        zipFileLocation = os.path.join( outFolder, uniqueShapeFile + descrip + '.zip')

        # Make a zip file object for each uniqueShapeFile
        z = zipfile.ZipFile( zipFileLocation, 'w')

        # for each file in the working directory
        for file in os.listdir( os.getcwd() ):

            # Split it at the '.'
            compFile = file.split('.')

            # if it's a zip file don't mess with it
            if file.endswith('.zip'):
                pass

            # if it's a file geodatabase don't mess with it. We'll deal with it later
            elif file.endswith('gdb') :

                file_zip_name = os.path.splitext( file )[0]

                # Zip file location for each uniqueShapeFile
                zipFileLocation = os.path.join( outFolder, file_zip_name + descrip + '.zip')

                # Make a zip file object for each uniqueShapeFile
                z = zipfile.ZipFile( zipFileLocation, 'w')

                # Get all the files in the directory
                for infile in glob.glob( file + "/*" ):

                    # write each of the files to the zip archive. 
                    z.write(infile, os.path.join( os.path.basename( file ), os.path.basename( infile ) ), zipfile.ZIP_DEFLATED)
             
                # close the zip archive
                z.close()

                # delte the file geodatabase
                shutil.rmtree(file)

            # if the file (without the extension) is the same as the 'uniqueShapeFile' then add it to the zip archive
            elif compFile[0] == uniqueShapeFile:

                # Add it to the zipfile object
                z.write(file)

                # Then remove the file
                os.remove(file)

            else:
                pass

        # close the zipfile object
        z.close()


def parse_csv( fileLocation, Unique_Features=None ):
    """
    Parses the csv file. Grabs the column headers. Gets a list of unique
    polylines from csv file
    """

    print 'Parsing CSV: ', fileLocation

    headers = []

    # Change directory to the folder
    os.chdir( os.path.dirname( fileLocation) )

    # grab all the rows in the csv file
    coordFileToList = [ line for line in csv.reader(open( fileLocation, 'r')) ]

    # grabs the csv column headers 
    headers = coordFileToList[0]

    # deletes list item, because it will get in the way later on if we don't
    del coordFileToList[0]

    # file name without the extension and minus the path
    rootFileName = os.path.splitext( os.path.basename( fileLocation ))[0]

    # If parsing csv for polylines or polygons
    if Unique_Features == True:

        # For kml_to_line and kml_to_polygon. Not used for kml_to_point. List 
        # of names of the unique spatial feataures in csv file
        Unique_Features = list(set( [each[0] for each in coordFileToList ] ))

        return coordFileToList, rootFileName, headers, Unique_Features

    else:
        
        return coordFileToList, rootFileName, headers


def remove_hanging_spaces_headers( headers ):

    """
    Checks to make sure that there are no blank spaces on the last header. If so,
    it was probably an error, so delete it
    """

    hangingSpaces = re.findall( r'^[\s]+$', headers[ -1: ][ 0 ] )

    # If it does have one or more white spaces then
    if hangingSpaces:

        # delete it
        del headers[-1:]

    # If it is not white spaces check to see if it is empty. if so, then
    elif headers[-1:][0] == '':

        # delete it
        del headers[-1:]

    return headers


def remove_hanging_spaces_rows( coordFileToList, header_length ):

    """
    Checks to see if the rows(self.coordFileToList) 
    are longer than the attribute headers (i.e self.shortGisFields).
    If it is then it is probably a 'hanging cell', meaning it is not part of the data set.  
    """

    # Loop over each list in the list
    for index, table_row in enumerate( coordFileToList ):

        # If length of the field is longer than the attribute header names
        if len( table_row ) > header_length:

            # Generate the proper number to use to slice out the hanging cell
            forSlice = len( table_row ) - header_length

            # Assign the proper items to the list, excluding the hanging cells
            coordFileToList[ index ] = table_row[ :-forSlice ]

    return coordFileToList

