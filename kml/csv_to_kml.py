import os, pdb
from pygis.kml.kml_utilities import make_kml
from pygis.shapefile.shapefile_utilities import parse_csv, remove_hanging_spaces_headers, remove_hanging_spaces_rows

class Csv_To_Kml:

    def __init__( self, filesLocation, outFolderKml, **kwargs ):

        """
        This script gnerates a kml from a csv file that has line data (i.e. a bunch of coordinates that are to 
        be drawn as a line. There can be many lines in the csv file so long as the first column
        contains the polyline name.  A line will be created for each distinct item in this column
        The longitude has to be the second to last column and the latitude has to be
        the last column.  The coordinates (i.e. the rows) have to be in order in
        which the line needs to be drawn. If a column header is titled
        'description', then that text will be written to the bubble that
        appears in Google Earth when you click on the object. The description
        text for each polyline has to be the same text, because you describing
        the line and not a point. If there are any other columns they will be
        ignored.

        The csv should be formatted like. Important if you want a description associated with
        a line or polygon, then the column header 'description' has to be spelled exactly like this
        and be the second column:

        Transect, description,  Longitude, Latitude
        Altamaha, descrpt text about Altamaha ,  -81.234  , 31.345
        Altamaha, descrpt text about Altamaha,  -81.235  , 31.346
        Altamaha, descrpt text about Altamaha,  -81.236  , 31.347
        Altamaha, descrpt text about Altamaha,  -81.237  , 31.348
        Ogeechee, descrpt text about Ogeechee,  -81.244  , 31.345
        Ogeechee, descrpt text about Ogeechee,  -81.254  , 31.345
        Ogeechee, descrpt text about Ogeechee,  -81.264  , 31.346
        Ogeechee, descrpt text about Ogeechee,  -81.274  , 31.347
        St.Mary , descrpt text about St.Mary,  -81.335  , 31.346
        St.Mary , descrpt text about St.Mary,  -81.436  , 31.347
        St.Mary , descrpt text about St.Mary,  -81.537  , 31.348

        The output would be one kml file with three polylines(placemarks)
        1)Altamaha, 2) Ogeeche,3) St.Mary. There would be a description in each
        bubble for each placemark.

        'fileLocation' is the path to to where the csv file that you want to
        convert to kml are located. 'outFolderKml' is where you want to save
        the newly created kmls to. For example:
       
        filesLocation = 'C:\Path\To\csvfile.csv'
        outFolderKml = 'C:\Path\To\outPutKml' 
        """

        self.filesLocation = filesLocation
        self.outFolderKml = outFolderKml
        self.kwargs = kwargs

        # Invoke module from shapefile_utilities to parse csv file and assign variables
        self.coordFileToList, self.rootfileName, self.bubbleFields, self.UniqueLines = parse_csv( filesLocation, Unique_Features=True )
        self.kmlFileName = self.rootfileName + '.kml'


        # If kwargs 'cleanup_data' is True then check for hanging cells in headers and bubbleFields.
        # A hanging cell is essentially a typo where a user enters a space at the end of the row
        # whereas the user intends the cell to have no data.  
        if 'cleanup_data' in self.kwargs and self.kwargs[ 'cleanup_data' ] == True:

            # Checks to make sure that there is not an extra cell with just black spaces for the last header
            remove_hanging_spaces_headers( self.bubbleFields )

            # Checks to make sure that all rows are the length of the header
            remove_hanging_spaces_rows( self.coordFileToList, len( self.bubbleFields) )

        # kwargs that has to be passed to the function that generates the kml so that it knows that
        # the data is coming from a csv file.  It has to be packaged accordingly, as opposed from
        # data that could be coming from a shapefile
        self.kwargs.update( { "parsed_csv" : self.UniqueLines } ) 


    def to_line(self, description_index=None):

        """
        Write the kml to file
        """

        geom_type = 'Polyline'

        # Call method in geospatial.kml.kml_utilities to create the line kml file
        make_kml( self.outFolderKml, self.kmlFileName, self.coordFileToList, geom_type, self.bubbleFields, **self.kwargs )

    def to_polygon(self, description_index=None):

        """
        Write the kml to file
        """

        geom_type = 'Polygon'

        # Call method in geospatial.kml.kml_utilities to create the line kml file
        make_kml( self.outFolderKml, self.kmlFileName, self.coordFileToList, geom_type, self.bubbleFields, **self.kwargs )

    def to_point(self):

        geom_type = 'Point'

        # Call method in geospatial.kml.kml_utilities to create point kml file
        make_kml( self.outFolderKml, self.kmlFileName, self.coordFileToList, geom_type, self.bubbleFields, **self.kwargs)


        





  


