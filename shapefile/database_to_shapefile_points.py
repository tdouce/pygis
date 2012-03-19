import os, pdb
from pygis.shapefile.shapefile_utilities import putBackLegals, make_shapefile_point_esri_v9, query_all_and_selected_and_make

def package_for_make_shapefile( allCoordList, querys):

    """
    Packages up a list that contains all the information needed to make a shapefile.
    The list has to be packaged up in specific manner and this function packages up the
    data recieved from the query in a proper format.
    """

    # A List to hold the lists: superCoordListName, superCoordList and querys
    bundle = []

    # Grab the shapefileName
    superCoordListName = [ allCoordList[0][0] ]

    # Grab the attribute table row data
    superCoordList = [ x[1:] for x in allCoordList]
    
    # Append it all to bundle for passing to makeShapefile method
    bundle.append( [superCoordListName, querys, superCoordList]  )

    return bundle



class Database_To_Shapefile_Points:

    """
    Summary:
    This script retrieves data from a database and makes shapefiles. This script
    will create many shapefiles and each shapefile  can contain one to many points. 
    Specifically, this  script makes a unique query to the database for each shapefile 
    and then makes a shapefile per query. The advantage of this approach is that
    that only data specific to each shapefile is held in memory at any given
    time. This is opposed to querying all the data for all the shapefiles from the 
    database and holding it all the data in memory.  The reason this approach was
    chosen was to more efficiently accomodate working with very large datasets.
    Note, there is an xml method  that allows the user to pass in a dictionary with 
    value and key pairs for data you want added to the xml metadata file and the script
    will edit the metadata (xml file), thus adding the queryied data. Currently
    the script does NOT query metadata specific to each shapefile, but rather
    applies the dictionary data to ALL the shapefiles.  

    Prerequisite for script:
    All data (points,Accession,Vertex, etc.) are stored in a database table or view. Database columns
    names are used in the sql query and are used to name the columns in the attribute table in ArcGIS. 
    ATTENTION: The table or view that is created SHOULD NOT have column names longer than 10
    characters because ArcGIS will not accept them.  To cirumvent this issue, make a column name alias less than
    10 charachers long. If column names are longer than 10 characters this script will truncate the column names
    at 10 characters.  Also, ArcGIS only accepts alphanumeric characters in the column names. Please
    replace any illegal characters in the table view.  If you do not, this script will replace the illegal
    characters with a '_' and you can NOT replace them the original state later in the script. ArcGIS, also only
    allows alphanumeric characters in the shapefile name.  You can replace illegal characters in the script in the
    function 'illegals()'.

    
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


    Consider the following data base structure:

    Accession       Description           SiteCode     Longitude   Latitude
    NUT-GCEM-0210   Some description_1    ALT-BASIN    -81.4356    31.5256 
    NUT-GCEM-0210   Some description_2    ALT-BASIN    -81.2356    31.1256 
    NUT-GCEM-0210   Some description_3    ALT-BASIN    -81.62356   31.3256 
    PLT-GCET-0608   Some description_1    CentralCst   -81.7468    31.980  
    PLT-GCET-0608   Some description_1    CentralCst   -81.7468    31.980  
    HYD-GCES-0508b  Some description_1    CentralCst   -81.7834    31.8778


    This script would output the following:
    1) If the variable 'IndvQueryShapefileName' was passed in as an empty list,
    and 'SiteCode' was passed in as 'polygonDeciderColumn', then
    the a 3 Shapefiles would be created, NUT-GCEM-0210 (3 points in shapefile), 
    PLT-GCET-0608 (2 points in shapefile), and  HYD-GCES-0508b ( 1 point in
    shapefile). 
    2) If the variable 'IndvQueryShapefileName' was passed in with items in the
    list (such as 'NUT-GCEM-0210' and 'HYD-GCES-0508b'), then two shapefiles
    would be created,'NUT-GCEM-0210'(3 points in shapefile) and 'HYD-GCES-0508b'(
    one point in shapefile)

    Other Need to knows:
    1) This script only works for POINTS, not polygons or polylines
    2) The sql query is automatically generated based on the user input.  
    3) The ArcGIs attribute field names are automatically generated based on user input.
    4) The script will detect 'String','Integer',and 'float',' data types from the database.  Corresponding
    attribute table fields with datatypes of 'long','double',and 'text' will be created in GIS.  All other data types
    will be converted to 'text' in ArcGIS. 
    5) This script processes one shapefile at a time so that only the data
    associated with a particular shapefile will be held in memory at one time.
    This would would allow an enormous amount of shapefiles to be created.
    """
    

    def make_shapefile( self, databaseCnxnInfo, databaseTable,
            shapefileColumnName, IndvQueryShapefileName, pointDeciderColumn,
            queryingColumns, Lat, Long, coordsys,  outFolder, metadataDict, **kwargs ):
        

        # Calls generic function to generate shapefiles, but 'EsriMakeShapePolygon' and
        # 'package_for_makeShapefile' allows the code to be customized
        query_all_and_selected_and_make( 
                                         databaseCnxnInfo, databaseTable, shapefileColumnName, shapefileColumnName,
                                         IndvQueryShapefileName, pointDeciderColumn, queryingColumns, Lat, Long, coordsys,
                                         outFolder, metadataDict, package_for_make_shapefile,
                                         make_shapefile_point_esri_v9, **kwargs 
                                       ) 


    def putBackLegals( self, outFolder, putBack=None ):


        if putBack == None:
            pass

        else:

            putBackLegals( outFolder, putBack )

        



