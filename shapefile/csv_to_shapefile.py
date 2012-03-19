import os, arcgisscripting, csv, re, pdb
from pygis.shapefile.metadata import make_shapefile_metadata
from pygis.shapefile.shapefile_utilities import parse_csv, create_file_and_projection_esri_v9, remove_hanging_spaces_headers, remove_hanging_spaces_rows, replace_values_helper, replace_values, sanitize_filename, sanitize_header, make_shapefile_array_esri_v9, make_shapefile_point_shape_esri_v9, make_shapefile_array_line_esri_v9

def deep_data_type( gp, outFile, dataTypeTracker, shortGisFields, coordFileToList ):

    """
    Summary:  This is a function that is available to the shapeFileMaker class
    that detects more in-depth the data types that are in a column.  It
    inspects every single row in a column to see what type of data is in it.
    Once the data type of the column is determined, the appropriate attribute
    column headers are created in ArcGIS and a dictionrary 'dataTypeTracker' is
    returned to help set row values on the attribute column in ArcGIS is


    'gp' = is the arcscripting geoprocessor object

    'dataTypeTracker' - An empty dictionary

    'shortGisFields' - A list of items that will eventually become the ArcGIS
    attribute column headers'

    'coordFileList' - This is all the data that will be used to create the
    shapefile, minus the 'shortGisFields'
    
    """

    # Gets all the data per column (as it appears in the csv file) 
    rows = ([row[idx] for row in coordFileToList] for idx in range( len(coordFileToList[0]) ))

    cntrData = 0 

    # for each list in 'rows'
    for row in rows:

        # Puts the entire list to a string so it will be easy to run regex on
        typeChecker = ''.join( row )

        # RE to to figure out data types.  Searches for anything that is NOT integer or float data type 
        pat = r'[^\s0-9.-]+'
        findall = re.findall(pat, typeChecker)

        # if the above pattern is found that means it has to be a text type column
        if findall:

            # Assign it to the dictionary
            dataTypeTracker[ shortGisFields[cntrData] ] = 'Text'

            # Create the attribute column in ArcGIS
            gp.addfield(outFile, shortGisFields[cntrData], "text", "20","20", "250", "#", "#", "#", "#")

            # Add one to the counter
            cntrData += 1

        
        # From what is left over, if there is '.' found in the string then it has to be a float
        elif '.' in typeChecker:

            # Assign it to the dictionary
            dataTypeTracker[ shortGisFields[cntrData] ] = 'Float'

            # Then create an attribute table column with the data type 'DOUBLE'
            gp.addfield(outFile, shortGisFields[cntrData], "DOUBLE", "20","20", "#", "#", "#", "#", "#")

            # Add one to the counter
            cntrData += 1

        elif typeChecker == '':

            dataTypeTracker[ shortGisFields[cntrData] ] = 'Text'

            gp.addfield(outFile, shortGisFields[cntrData], "text", "20","20", "250", "#", "#", "#", "#")

            cntrData += 1

        # What's left has to be an integer
        else:

            # Assign it to the dictionary
            dataTypeTracker[ shortGisFields[cntrData] ] = 'Integer'

            # Then create an attribute table column with the data type # 'LONG'
            gp.addfield ( outFile, shortGisFields[cntrData], "LONG", "20","20", "15", "#", "#", "#", "#")

            # add one to the conter 
            cntrData += 1


    # return the dictionary so it can used used to set the values on the column
    return dataTypeTracker


def check_reserved_headers( shortGisFields, reserved ):

    # Dictionary to hold alterted reserved words. ArcGIS will not allow the items in the reserved list to be used as attribute
    # header names.  So, if we find an incompatible match then we append a '_' to it so it is recognizable to the user and a valid
    # attribute header name in ArcGIS
    reserve_dict = {}

    # Add each word reserved list to reserved_dict with a '_' appended to it
    [ reserve_dict.update( { word : word + '_' } ) for word in reserved ]

    # Add '' key to reserve_dict with value of 'None_'
    reserve_dict[''] = 'None_'

    # Replace values in dictionary if found in shortGisFields
    shortGisFields = replace_values( shortGisFields, reserve_dict )

    return shortGisFields

 
def check_numbers_at_beginning( shortGisFields, max_field_length ):

    """
    Check to see if the ArcGIS column headers
    begin with a number, of which they can NOT.  This code checks for
    this condition and if it does begin with a number it prepends an '_'
    to the column name, and then checks for the length (ArcGIS will not
    allow it to be  longer than 10 characters).  If it is longer than 10
    characters it replaces the middle value.  The reason it replaces the
    middle value is because if we cut off the last few characters to make
    it 10 characters in length there could very possibly be duplicate
    header names (which ArcGIS does not allow). So, it takes about the
    middle character so hopefully the header will remain recognizable,
    but yet still be valid
    """

    for index, field in enumerate( shortGisFields ):
      
        if field[ 0 ] in str( range(10) ):

            # Prepend a '_' to it
            shortGisFields[ index ] = '_' + field

            # Check the length
            if len( shortGisFields[index] ) > max_field_length:

                # Find the index to replace
                forReplace = ( len( shortGisFields[ index ] )/2 )

                # Replace the index with ''
                shortGisFields[ index ] = shortGisFields[ index ].replace( shortGisFields[ index ][ forReplace ], '' )

    return shortGisFields



def check_for_duplicate_headers( shortGisFields ):

    """
    Checks for duplicate headers.  ArcGIS does not allow duplicate header names in the attribute table
    """

    # A dictionary to hold every item in self.shortGisFields.
    fieldDict = {}

    # A list that holds the adjusted attribute header names
    no_duplilcates_shortGisFields = []

    for field in shortGisFields:

        # if field appears in the dictionary...meaning we have already seen it once
        if field in fieldDict:

            # Then assign the number of times we have seen it to the value
            fieldDict[ field ] = fieldDict[ field ] + 1

            # Make the string that will be appended to it
            toAppend =  str( fieldDict[ field ] )

            # Get the length of what will be appended to it. This is
            # necessary because we have to subract this length from the
            # root of the attriute header name
            lenToAppend = len( toAppend )

            # Append the newly adjusted attribute header name, which is the
            # 'toAppend' string and the field minus the length of the 'toAppend' string
            no_duplilcates_shortGisFields.append( field[ :-lenToAppend ] + toAppend )

        # If the field is not in the dictionary then we have not seen it
        # before and assign it one and append it as it is to the list
        else:

            fieldDict[ field ] = 1
            no_duplilcates_shortGisFields.append( field )

    return no_duplilcates_shortGisFields



def sanitize( coordFileToList, shapefileName, gisFields, kwargs ):

    print 'Replacing any illegals characters'

    # If we are making a filegeodatabase, then we set the attribute table
    # field size to 64 or to 10 if we are making a shapefile
    if 'fileGDB' in kwargs:         

        max_field_length = 64

    else:

        max_field_length = 10

    # List of items that contains (as far as I know) all reserved
    # attribute column header names in ArcGIS.  This list will be used to
    # compare the headers parsed from the csv file and if a csv header is
    # found to match one of these items then a '_' will be appended to it.
    reserved = ['Date','FID','ID','Shape']
    
    # If the 'RowValueReplace' argument was pass in then replace the table row values with
    # the values in the 'RowValueReplace' dictionary
    if 'rows_replace' in kwargs:
        
        # Invoke function that implements numpy to loop through entire list and replace values
        # according to dictionary
        coordFileToList = replace_values( coordFileToList, kwargs['rows_replace'] )

    # If the 'AttrheaderReplace' argument was passed in then it is used to replace the the
    # headers.  If the 'AttrheaderReplace' was NOT passed in then the headers are truncated at 10 characters. 
    if 'header_replace' in kwargs:

        shortGisFields = replace_values( gisFields, kwargs['header_replace'] )

    else:
        shortGisFields = gisFields


    if 'cleanup_data' in kwargs and kwargs[ 'cleanup_data' ] == True:

        # Checks to see if the last cell in the attribute header names is empty or has white space(s). 
        # If the last header is a 'hanging cell' then delete it 
        shortGisFields = remove_hanging_spaces_headers( shortGisFields )

        # Checks to see if the length of the tables rows (minus the header) are equal to the header.
        # If they are not the same length, it most likely means that there is a 'hanging cell' (i.e. white space).
        # and remove the last table cells until they are the same length as the headers. 
        coordFileToList = remove_hanging_spaces_rows( coordFileToList, len(shortGisFields ) )

    # Check to see if any reserved terms are used in the headers/self.shortGisFields
    shortGisFields = check_reserved_headers( shortGisFields, reserved )

    # Check for non-permitted values and length (not longer than 10 characters) in the csv headers/self.shortGisFields/ArcGis attribute table headers
    shortGisFields = sanitize_header( shortGisFields, '_', max_field_length )

    # Checks to see if the csv headers/self.shortGisFields/ArcGis attribute table headers 
    # begin with a number (They can NOT begin with a number. If a header does begin with a number it prepends an '_'
    # to it, and then checks for the length (ArcGIS will not
    # allow it to be  longer than 10 characters).  If it is longer than 10
    # characters it replaces the middle value.  The reason it replaces the
    # middle value is because if we cut off the last few characters to make
    # it 10 characters in length there could very possibly be duplicate
    # header names (which ArcGIS does not allow). So, it takes about the
    # middle character so hopefully the header will remain recognizable, but yet still be valid
    shortGisFields = check_numbers_at_beginning( shortGisFields, max_field_length )
    
    # Checks for duplicates in the csv headers/self.shortGisFields/ArcGis attribute table headers
    shortGisFields = check_for_duplicate_headers( shortGisFields )

    # Check for non-permitted values in shapefile name. If one is found then replace it with a
    gisShapefileName = sanitize_filename( shapefileName, '__' )


    # Checks to see if the length of the tables rows (minus the header) are equal to the header.
    # If they are not the same length, it most likely means that there is a 'hanging cell' (i.e. white space).
    # and remove the last table cells until they are the same length as the headers. 
    #coordFileToList = remove_hanging_spaces_rows( coordFileToList, len(shortGisFields ) )

    return shortGisFields, coordFileToList, gisShapefileName


def make_shapefile_attr_table_columns_esri_v9_csv( gp, coordFileToList, shortGisFields, outFile, **kwargs ):

    # Make a copy of the first item in 'self.coordFileList' so we can use
    # it to iterate over and determine data types for the attribute table columns
    first_data_table_row = list( coordFileToList[ 0 ] )
   
    # An empty dictionary that will be used to track what datatypes the
    # attribute columns are after they are created.  The results will be
    # used to help set the row values on this column later in the script
    dataTypeTracker = {}

    # If a keyword argument was passed in
    if kwargs and 'deep_data_type' in kwargs:

        # If a keyword argument of 'deepDataType=True' was passed in
        if kwargs['deep_data_type'] == True:

            # Then invoke the 'deepDataType' function
            deep_data_type( gp, outFile, dataTypeTracker, shortGisFields, coordFileToList)

    # If 'deep_data_type' was not passed in and determine attribute table fields on the first
    # table data row and create them 
    else:

        index_sync = 0

        for row_value in first_data_table_row:
            
            # Take off any extra white spaces
            row_value = row_value.strip(' ')

            # RE to to figure out data types.  Searches for anything that is NOT integer or float data type 
            pat = r'[^0-9.-]+'

            findall = re.findall( pat, row_value )

            try:

                # Will return True if it found anything that is NOT integers or
                # float data type (i.e. any letters or symbols)
                if findall:

                    dataTypeTracker[ shortGisFields[ index_sync ] ] = 'Text'

                    # if anything other than numbers was found make the data type a string
                    gp.addfield ( outFile, shortGisFields[ index_sync ], "text", "20","20", "250", "NULLABLE", "#", "#", "#")

                    # add one to the index1
                    index_sync += 1

                # If only integers or float data types were found
                else:

                    # If the cell was emtpy make it a text data type
                    if row_value == '':

                        dataTypeTracker[ shortGisFields[ index_sync ] ] = 'Text'

                        # This lets the fields be nullable if created in a  geodatabase
                        gp.addfield ( outFile, shortGisFields[ index_sync ], "text", "20","20", "#", "#", "NULLABLE", "#", "#")

                        index_sync += 1

                    # if each has a decimal in it (ie a float) then make the data type a 'double'
                    elif '.' in row_value:
                        
                        row_value = float( row_value )

                        dataTypeTracker[ shortGisFields[ index_sync ] ] = 'Float'

                        # Then create an attribute table column with the data type 'DOUBLE'
                        gp.addfield ( outFile, shortGisFields[ index_sync ], "DOUBLE", "20","20", "#", "#", "NULLABLE", "#", "#")

                        index_sync += 1

                    # if the it doesn't have a decimal point then it must be an integer, so make the column a 'long' integer
                    else:

                        # Convert each to an integer data type
                        row_value = int( row_value )

                        dataTypeTracker[ shortGisFields[ index_sync ] ] = 'Integer'

                        # Then create an attribute table column with the data type # 'LONG'
                        gp.addfield ( outFile, shortGisFields[ index_sync ], "LONG", "20","20", "15", "#", "NULLABLE", "#", "#")
                        
                        index_sync += 1
            except:

                dataTypeTracker[ shortGisFields[ index_sync ] ]

                gp.addfield ( outFile, shortGisFields[ index_sync ], "text", "20","20", "#", "#", "#", "#", "#")

                index_sync += 1

    return dataTypeTracker


def make_shapefile_attr_table_rows_esri_v9_csv( cur, row, shortGisFields, dataTypeTracker, line ):

    """
    Sets values in the ArcGIS attribute table
    """

    index_setValue_sync = 0

    for field in shortGisFields:

        # Get the data type of the column in which it belongs, which is
        # recorded in the 'dataTypeTracker' dictionary
        dataType = dataTypeTracker[ shortGisFields[ index_setValue_sync ] ]

        # If it is an integer data type
        if dataType == 'Integer':

            # Try to assign it the value
            try:

                line[ index_setValue_sync ] = int( line[ index_setValue_sync ] )

                # Sets the values to the cooresponding row
                row.SetValue( shortGisFields[ index_setValue_sync ],line[ index_setValue_sync ])
                            
                #Add one to count so we can go to the next index
                index_setValue_sync += 1

            # If the value fails or if the value is empty, then assign
            except:

                # try to input a null value.  This will only work if
                # using a file geodatabase
                try:
                    #Add one to count so we can go to the next index
                    index_setValue_sync += 1

                # if a null value can not be assigned then assign a
                # zero.  This should work for .shp files
                except:

                    # Sets the values to the cooresponding row
                    row.SetValue( shortGisFields[ index_setValue_sync ], int(0))

                    #Add one to count so we can go to the next index
                    index_setValue_sync += 1

        # if it is a float
        elif dataType == 'Float':

            # Try to assign it the value 
            try:

                line[ index_setValue_sync ] = float( line[ index_setValue_sync ] )

                # Sets the values to the cooresponding row
                row.SetValue( shortGisFields[ index_setValue_sync ],line[ index_setValue_sync ])
                            
                #Add one to count so we can go to the next index
                index_setValue_sync += 1
           
            # If the value fails or if the value is empty, then assign
            except:

                # try to input a null value.  This will only work if
                # using a file geodatabase
                try:
                                
                    #Add one to count so we can go to the next index
                    index_setValue_sync += 1

                # if a null value can not be assigned then assign a
                # zero.  This should work for .shp files
                except:

                    # Sets the values to the cooresponding row
                    row.SetValue( shortGisFields[ index_setValue_sync ], float(0) )
                                
                    #Add one to count so we can go to the next index
                    index_setValue_sync += 1

        # If it is text
        elif dataType == 'Text':

            # Try to assign the value
            try:

                line[ index_setValue_sync ] = str( line[ index_setValue_sync ] )

                # Sets the values to the cooresponding row
                row.SetValue( shortGisFields[ index_setValue_sync ],line[ index_setValue_sync ])

                #Add one to count so we can go to the next index
                index_setValue_sync += 1

            # If the value fails or if the value is empty, then assign
            except:

                # try to input a null value.  This will only work if
                # using a file geodatabase
                try:
                    #Add one to count so we can go to the next index
                    index_setValue_sync += 1

                # if a null value can not be assigned then assign a
                # zero.  This should work for .shp files
                except:
                    # Sets the values to the cooresponding row
                    row.SetValue( shortGisFields[ index_setValue_sync ], 'no text')

                                
                    #Add one to count so we can go to the next index
                    index_setValue_sync += 1


def make_polyline_polygon( gisShapefileName, outFolder, coordsys, geomType,
                           coordFileToList, shortGisFields, UniqueLines, keywords_args ):

    self_kwargs = keywords_args[ 'self_keywordargs' ]
    kwargs      = keywords_args[ 'keywordsargs' ]   

    # Assign variables and invoke function that generates the shapefile or
    # filegeodatabase/featureclasses and assignes the projection
    gp, outFile      = create_file_and_projection_esri_v9( gisShapefileName, outFolder, coordsys, geomType, **self_kwargs )

    # Get coords minus the latitude and longitude coordinates.  You can't display these for
    # polygons in the attribute table because there are many points for each polygon.
    coords_to_list_no_lat_long = [ coord[:-2] for coord in coordFileToList ]
    
    # Make attribute table columns with appropriate datatype
    dataTypeTracker = make_shapefile_attr_table_columns_esri_v9_csv( gp, coords_to_list_no_lat_long, shortGisFields[:-2], outFile, **kwargs )
    
    for unique in UniqueLines:
        
        # Get only the coordinates for the feature( i.e. unique )
        coordinates = [ coord[-2:] for coord in coordFileToList if coord[0] in unique ]

        if geomType == 'POLYLINE':

            # Make point array
            cur, row = make_shapefile_array_line_esri_v9( gp, coordinates, outFile )

        if geomType == 'POLYGON':

            # Make point array
            cur, row = make_shapefile_array_line_esri_v9( gp, coordinates, outFile )

        # Get all data except for the coordinates
        lines = [ coord for coord in coordFileToList if coord[0] in unique ]

        # Insert row values
        for line in lines:

            make_shapefile_attr_table_rows_esri_v9_csv( cur, row, shortGisFields[:-2], dataTypeTracker, line[:-2] )

        # ArcGIS Reqruiement: Step 5: Commit row to dataset
        cur.InsertRow(row)

    # delete cur and row so you don't lock things up
    del cur,row

    return outFile



class Csv_To_Shapefile:

    '''
    Summary: This class takes a csv file and converts it to an ESRI ArcGIS
    shapefile.  The script determines datatypes for the attribute table in
    ArcGIS based on characteristics of the table row text. The following data types are recognized: 
    'text','double', and 'long' data types.  For this script to work, the last
    two columns of the csv file have to be (in this order) 'Longitude' and 'Latitude'.  
    These two columns can be named anything you like so long as
    they occur in this order.  The shapefile name is derived from the csv file
    name.  There is one quirk with this script.  If in the csv file a row was
    entered and then deleted, thre is actually something in the row although it
    is not apparent.  Python will read it because there is something there and
    the result is that it will blow up.  Copy just the content into a new
    file and use that new csv file.

    This class takes one argument at instantiation.

    'fileLocation' - The location of the csv file you want to convert to an
    ArcGIS file

    Output - The output of the class is an ESRI ArcGIS shapefile


    'fileGDB' - This is an optional kwarg argument that tells the script 1) that we
        want to create a file geodabase and we want to add feature
        classes to it, as opposed to a shapefile; and 2) to cut off the attribute table fields names at 
        a specific length for either shapefile or file geodatabases.  
        Shapefiles can only have attribute table field names up to 10 characters 
        long, while file geodatabases can have attribute table field names 
        upto 65 characters long. If fileGBD is set to True then it will allow 
        upto 64 characters in length to be maintained. For example,

            fileGDB = 'File_geodatabase_name.gdb'

    'AttrHeaderReplace' - This is an optional parameter.  The dictionary contains
        alternate spellings (that will appear in the ArcGIS attribute header
        name). The keys in the dictionary are is the header that you want to
        replace.  It has to be spelled exactly the same as it appears in the
        .csv file.  The value is what you want to be spelled like in the ArcGIS
        attribute table.  The key has to be 10 or less characters in length.
        For example:

            ForReplace = {'AveryLongHeaderName': 'altrnateNm',
                           'AnotherLongHeaderName': 'AltrNm_2',
                         }

            AttrHeaderReplace=ForReplace

        'RowValueReplace' - This is an optional argument that allows you to
        pass in a dictionary for that contains key value pairs that will be
        used to replace row cell values.  The key is
        what you want replaced and the value is what you want it to be replaced
        with. All keys and values MUST be strings.  

            headerReplace = {'NaN': '0', '--','null'}

            RowValueReplace=headerReplace

    '''

    def __init__(self, fileLocation, outFolder, coordsys, **kwargs ):

        self.fileLocation = fileLocation 
        self.kwargs = kwargs
        self.outFolder = outFolder
        self.coordsys = coordsys
        
        # Parse csv file and assign variables
        self.coordFileToList, self.shapefileName, self.gisFields, self.UniqueLines = parse_csv( self.fileLocation, Unique_Features=True )

        # Invoke sanitize method
        self.__sanitize() 

    def __sanitize(self ):

        """
        Summary: This method replaces illegal characters in the attribute/columns.
        It also allows the user to pass
        in a Dictionary of prefered attribute/column names.  If a dictionary is
        not passed in then the attribute headers are truncated to 10 characters
        in length because ArcGIS will not allow them to be longer than 10
        characters.  If an attribute header is truncated at 10 characters and
        it happens to be the named the same as another header column then it
        will append an '_' with a counter to it, and shortening the root
        attribute header name so that the attribute header is still less than
        10 characters in length. If you have a lot of attribute headers that
        will be truncated it is recommended to pass in a dictionary with
        alternate spellings.
        """

        self.shortGisFields, self.coordFileToList, self.gisShapefileName = sanitize(
                self.coordFileToList, self.shapefileName, self.gisFields, self.kwargs )


    def make_shapefile_point(self, **kwargs):
        
        """
        Summary: This method does the actual making of the point shapefile in ArcGIS.
        This method takes two arguments. If 'deep_data_type' is not passed in, then 
        the datatypes for the ArcGIS attribute table fields will be determined
        by the first table row (that is not the header).

        'outFolder' - The location where you want the shapefile saved to. If
        you created a file geodatabase and want to add featureclass to it, then
        'outFolder' should be the path to the filegeodatabase.

        'coordsys' - The location on the local computer where the ESRI coordinate
        system file is located. This is in the ESRI files. It would be
        something simliar to:

            coordsys = 'C:\\Program Files\\ArcGIS\\Coordinate Systems\\Geographic Coordinate Systems\\World\\WGS 1984.prj'

        'deep_data_type' - This is an optional argument.  If it is passed in as
        'True' then deep detection will occur that inspects every row in a
        column to determine more precisely what datatype the column should be
        assigned in ArcGIS.  If it is not passed in a more superficial data
        type detection will occur, which only inspects the first row of a
        column to determine what datatype it is. For example:

            deep_data_type=True
        
        """

        # The geomType the shapefile will be
        geomType = "POINT"

        # Assign variables and invoke function that generates the shapefile or
        # filegeodatabase/featureclasses and assignes the projection
        gp, self.outFile = create_file_and_projection_esri_v9( self.gisShapefileName, self.outFolder, self.coordsys, geomType, **self.kwargs )

        ############# Adding Attribute Table Fields ############
        # This adds fields. Create a field for each item in 'shortGisAttributeTableFields'.
        # Form more information about adding Fields see:
        # http://webhelp.esri.com/arcgisdesktop/9.3/index.cfm?TopicName=Add_Field_%28Data_Management%29
        dataTypeTracker = make_shapefile_attr_table_columns_esri_v9_csv( gp, self.coordFileToList, self.shortGisFields, self.outFile, **kwargs )
                                                                        
        # Variable to keep track (for print) of how many points were added for each shapefile       
        self.Point_Count = 1

        # for each line in 'coordFileToList'
        for line in self.coordFileToList:

            # Create the point shape
            cur, row = make_shapefile_point_shape_esri_v9( gp, line[-2:], self.outFile )
           
            # Variable that helps synchronize the indexs for setting data in the attribute table rows
            index_setValue_sync = 0

            # Insert row values
            for each in range( len( line ) ):

                index_setValue_sync = make_shapefile_attr_table_rows_esri_v9_csv( cur, row, self.shortGisFields, index_setValue_sync, dataTypeTracker, line )

            # ArcGIS Reqruiement: Step 5: Commit row to dataset
            cur.InsertRow(row)

            # Add one to the 'Count' variable. Keeping track of how many points were added for each shapefile 
            self.Point_Count += 1
                   
        # ArgGis requirement: delete cursor and row so you don't lock ArcGIS
        del cur,row
        
        print self.outFile,'created.'


    def make_shapefile_polygon(self, **kwargs):

        """
        Summary: This method does the actual making of the polygon shapefile in ArcGIS.
        This method takes two arguments. If 'deep_data_type' is not passed in, then 
        the datatypes for the ArcGIS attribute table fields will be determined
        by the first table row (that is not the header).

        'outFolder' - The location where you want the shapefile saved to. If
        you created a file geodatabase and want to add featureclass to it, then
        'outFolder' should be the path to the filegeodatabase.

        'coordsys' - The location on the local computer where the ESRI coordinate
        system file is located. This is in the ESRI files. It would be
        something simliar to:

            coordsys = 'C:\\Program Files\\ArcGIS\\Coordinate Systems\\Geographic Coordinate Systems\\World\\WGS 1984.prj'

        'deep_data_type' - This is an optional argument.  If it is passed in as
        'True' then deep detection will occur that inspects every row in a
        column to determine more precisely what datatype the column should be
        assigned in ArcGIS.  If it is not passed in a more superficial data
        type detection will occur, which only inspects the first row of a
        column to determine what datatype it is. For example:

            deep_data_type=True
        
        """

        # The geomType the shapefile will be
        geomType = "POLYGON"

        keywords_args = {}
        keywords_args[ 'self_keywordargs' ] = self.kwargs
        keywords_args[ 'keywordsargs' ]     = kwargs

        self.outFile = make_polyline_polygon( self.gisShapefileName, self.outFolder, self.coordsys, geomType,
                                              self.coordFileToList, self.shortGisFields, self.UniqueLines, keywords_args )


    def make_shapefile_polyline(self, **kwargs):

        """
        Summary: This method does the actual making of the polygon shapefile in ArcGIS.
        This method takes two arguments. If 'deep_data_type' is not passed in, then 
        the datatypes for the ArcGIS attribute table fields will be determined
        by the first table row (that is not the header).

        'outFolder' - The location where you want the shapefile saved to. If
        you created a file geodatabase and want to add featureclass to it, then
        'outFolder' should be the path to the filegeodatabase.

        'coordsys' - The location on the local computer where the ESRI coordinate
        system file is located. This is in the ESRI files. It would be
        something simliar to:

            coordsys = 'C:\\Program Files\\ArcGIS\\Coordinate Systems\\Geographic Coordinate Systems\\World\\WGS 1984.prj'

        'deep_data_type' - This is an optional argument.  If it is passed in as
        'True' then deep detection will occur that inspects every row in a
        column to determine more precisely what datatype the column should be
        assigned in ArcGIS.  If it is not passed in a more superficial data
        type detection will occur, which only inspects the first row of a
        column to determine what datatype it is. For example:

            deep_data_type=True
        
        """

        # The geomType the shapefile will be
        geomType = "POLYLINE"

        keywords_args = {}
        keywords_args[ 'self_keywordargs' ] = self.kwargs
        keywords_args[ 'keywordsargs' ]     = kwargs

        self.outFile = make_polyline_polygon( self.gisShapefileName, self.outFolder, self.coordsys, geomType,
                                              self.coordFileToList, self.shortGisFields, self.UniqueLines, keywords_args )


    def make_metadata( self, metadataDict ):

        """
        Summary: This method takes populates the ESRI xml metadata file with
        the data contained in the 'metadataDict' dictionary that is passed in.
        The class uses a module 'make_shapefile_metadata' to dynamically
        call all the methods of the 'Esri_metadata' class and populate the xml
        file with the data passed in in the dictionary.
        
        'metadataDict' - The dictionary that contains the keys and values that
        will be used to populate the xml file.  It is imperative that the 
        dictionary keys be spelled exactly the same as the the 'Esri_metadata' 
        class's methods. 

        """

        # Building path to the xml file that will be worked on
        xmlFilePath = os.path.join( self.outFolder, self.outFile + '.xml')


        # This is calling the function 'make_shapefile_metadata' in the
        # library at 'from pygis.shapefile.metadata import make_shapefile_metadata'
        # This dynamically calls all the methods of the 'Esri_Metadata' class.
        # This is useful in other 'make_shapefile' classes so I made a module out of it.
        make_shapefile_metadata( xmlFilePath,  metadataDict )


        



    

if __name__ == '__main__':
    pass


