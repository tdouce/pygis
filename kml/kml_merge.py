import xml.etree.cElementTree as etree
from xml.parsers.expat import*
import os, pdb,re, random, string

def find_placemarks( Placemarks, current_file, etree, f, styling_xml=None, **kwargs ):

    """
    Function called to find the placemarks in a file if styling is not preserved
    """

    # for each Placemark
    for marks in Placemarks:

        # The all the children nodes of marks
        marks_children = marks.getchildren()

        # Loop through each child node
        for child in marks_children:

            # If the child node text is 'name'
            if child.tag.split('}')[1] == 'name':

                if kwargs.has_key('append_file_name') and kwargs['append_file_name'] == 'Yes':

                    # Assign a new child.text that is the => # 'the_file_name' + 'the orginal node text'
                    child.text =  current_file + ' : ' + child.text


            # If the child node text is 'name'
            elif child.tag.split('}')[1] == 'styleUrl':

                # Assign a new child.text that is the => # 'the_file_name' + 'the orginal node text'
                #print  child.text.replace('#','')

                if styling_xml != None:

                    styling_xml = styling_xml + styling_xml
            
        # Convert the placemark node to a string
        placemark_toString = etree.tostring( marks )

        # Removing the namespace information because there could be
        # many different namespaces (which are strings now), and do not
        # ( I believe ) actually act like namespaces
        placemark_toString = re.sub(r'ns\d:', "" , placemark_toString )

        # removing other namespace info in placemark
        placemark_toString = re.sub(r'xmlns.+"', "" , placemark_toString )
        
        # Write the placemark string to our new kml file
        f.write( placemark_toString )



def unique_name( name, dic, number_of_allowed_dups ):
    """
    Recursion function to generate unqiue id for styling nodes
    """

    # If dic has the key
    if dic.has_key( name ):

        # Remove any number generated from the random generation that may exist
        # at the end of the id
        try:

            key_base = [ name.split(str(n))[0] for n in range( 0, number_of_allowed_dups ) if str(n) in name ][0]

        # if key doesn't exist 
        except:
            key_base = name


        # Generate a new dic key
        new_key_base = key_base + str(random.randrange( 0, number_of_allowed_dups ))

        # call the recursion function
        return unique_name( new_key_base, dic, number_of_allowed_dups )


    else:

        # If dic does not have key then put it in there and return name
        dic[ name ] = 1

        return name




def styling( style, url_name, style_directory, **kwargs): 

    """
    Function to generate the sytling xml for each unique id. There is code in
    here for handling polygon styling, which isn't implemented currently.
    """
    

    # If there was no styling
    if kwargs.has_key('pushpin') and kwargs['pushpin']==True:

        placemark_styling_xml = """
    <StyleMap id="msn_%s">
            <Pair>
                <key>normal</key>
                <styleUrl>#sn_%s</styleUrl>
            </Pair>
            <Pair>
                <key>highlight</key>
                <styleUrl>#sh_%s</styleUrl>
            </Pair>
    </StyleMap>
    <Style id="sh_%s">
            <IconStyle>
                    <scale>1.3</scale>
                    <Icon>
                            <href>http://maps.google.com/mapfiles/kml/%s.png</href>
                    </Icon>
                    <hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>
            </IconStyle>
            <ListStyle>
            </ListStyle> 
    </Style>
    <Style id="sn_%s">
            <IconStyle>
                    <scale>1.1</scale>
                    <Icon>
                            <href>http://maps.google.com/mapfiles/kml/%s.png</href>
                    </Icon>
                    <hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>
            </IconStyle>
            <ListStyle>
            </ListStyle>
    </Style>""" % ( style, 
                    style, 
                    style, 
                    style, 
                    style_directory + '/' + url_name, 
                    style,  
                    style_directory + '/' + url_name 
                    )


    # If it is a polygon
    elif kwargs.has_key('polygon') and kwargs['polygon']==True:

        placemark_styling_xml = """
    <StyleMap id="msn_%s">
            <Pair>
                <key>normal</key>
                <styleUrl>#sn_%s</styleUrl>
            </Pair>
            <Pair>
                <key>highlight</key>
                <styleUrl>#sh_%s</styleUrl>
            </Pair>
    </StyleMap>
    <Style id="sh_%s">
            <IconStyle>
                    <scale>1.3</scale>
                    <Icon>
                            <href>http://maps.google.com/mapfiles/kml/%s.png</href>
                    </Icon>
                    <hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>
            </IconStyle>
            <ListStyle>
            </ListStyle> 
            <LineStyle>
                    <color>%s</color>
                    <width>%s</width>
            </LineStyle>
            <PolyStyle>
                    <color>%s</color>
            </PolyStyle>
    </Style>
    <Style id="sn_%s">
            <IconStyle>
                    <scale>1.1</scale>
                    <Icon>
                            <href>http://maps.google.com/mapfiles/kml/%s.png</href>
                    </Icon>
                    <hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>
            </IconStyle>
            <ListStyle>
            </ListStyle>
            <LineStyle>
                    <color>%s</color>
                    <width>%s</width>
            </LineStyle>
            <PolyStyle>
                    <color>%s</color>
            </PolyStyle>
    </Style>""" % ( style, 
                    style, 
                    style, 
                    style, 
                    style_directory + '/' + url_name,
                    kwargs['line_color'],
                    kwargs['line_width'],
                    kwargs['poly_color'],
                    style,
                    style_directory + '/' + url_name, 
                    kwargs['line_color'],
                    kwargs['line_width'],
                    kwargs['poly_color'],
                    )


    # If it is a polyline
    elif kwargs.has_key('polyline') and kwargs['polyline']==True:

        placemark_styling_xml = """
    <StyleMap id="msn_%s">
            <Pair>
                <key>normal</key>
                <styleUrl>#sn_%s</styleUrl>
            </Pair>
            <Pair>
                <key>highlight</key>
                <styleUrl>#sh_%s</styleUrl>
            </Pair>
    </StyleMap>
    <Style id="sh_%s">
            <IconStyle>
                    <scale>1.3</scale>
                    <Icon>
                            <href>http://maps.google.com/mapfiles/kml/%s.png</href>
                    </Icon>
                    <hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>
            </IconStyle>
            <ListStyle>
            </ListStyle> 
            <LineStyle>
                    <color>%s</color>
                    <width>%s</width>
            </LineStyle>
    </Style>
    <Style id="sn_%s">
            <IconStyle>
                    <scale>1.1</scale>
                    <Icon>
                            <href>http://maps.google.com/mapfiles/kml/%s.png</href>
                    </Icon>
                    <hotSpot x="20" y="2" xunits="pixels" yunits="pixels"/>
            </IconStyle>
            <ListStyle>
            </ListStyle>
            <LineStyle>
                    <color>%s</color>
                    <width>%s</width>
            </LineStyle>
    </Style>""" % ( style, 
                    style, 
                    style, 
                    style, 
                    kwargs['line_color'],
                    kwargs['line_width'],
                    style_directory + '/' + url_name, 
                    style,  
                    style_directory + '/' + url_name,
                    kwargs['line_color'],
                    kwargs['line_width'],
                    )

        
    return placemark_styling_xml
    

def poly_checker( et, name_space, marks_children):


    # Grab the node text for the <styleUrl>
    child = [ node for node in marks_children if node.tag.split('}')[1] == 'styleUrl' ][0]

    # build a unique string to search for in the regex
    style_attr_msn = 'id="' + child.text.replace('#','') + '"'

    # Find all the style nodes using the current namespace
    Style_map_nodes = et.findall('{%s}Document/{%s}StyleMap' % ( name_space, name_space ))

    # for each <StyleMap> node found
    for style in Style_map_nodes:

        # Convert node to string
        style = etree.tostring( style)

        # Check to see if this is the corresponding node
        msn_check = re.search( style_attr_msn , style )

        # If node found
        if msn_check:

            # Grab all the <pair> nodes
            pair_nodes = re.findall( r'styleUrl>.+styleUrl>', style ) 

            # If pair nodes found
            if pair_nodes:

                #print 'pair_nodes: ', pair_nodes

                # Grab each reference to the <style> node
                for pair in pair_nodes:

                    # grab all between node
                    pair = re.search( r'>(.+)</', pair ) 

                    # Get just the <style> node reference
                    pair = pair.group(1)
                    pair = pair.replace('#','')

                    # Go back to the original document and
                    # grab all the <style> nodes. Find all the style nodes using the current namespace
                    Style_nodes = et.findall('{%s}Document/{%s}Style' % ( name_space, name_space ))

                    # Loop through each style node
                    for style_node in Style_nodes:

                        # convert it to a string
                        style_node = etree.tostring( style_node )

                        # build the node attribute, this should be unique. Have to include
                        style_node_check = 'id="' + pair + '"'

                        # If the match is in the <style> node
                        if style_node_check in style_node:

                            # Get rid of all the spaces and returns to make the regex search easier
                            style_string = re.sub(r"\n*", "", style_node)
                            style_string = re.sub(r"\s*", "", style_string )
                            style_string = re.sub(r"ns\d:", "", style_string )

                            # Regex to search for # <LineStyle> and <PolyStyle>
                            line_style= re.search("LineStyle.*LineStyle", style_string) 
                            poly_color = re.search("PolyStyle.*PolyStyle", style_string) 

                            # if line_color is found grab the contents in the node. This should be the
                            # hexadecimal color code
                            if line_style:

                                line_color= re.search("<color>(.*)</color>", line_style.group()) 
                                if line_color:
                                    line_color= line_color.group(1)

                                line_width= re.search("<width>(.*)</width>", line_style.group()) 
                                if line_width:
                                    line_width= line_width.group(1)

                            # If it is not found the assign it a defulat line color and line width
                            else:

                                line_color = 'white'
                                line_width = '1'

                            # if poly_color is found grab the contents in the node. This should be the
                            # hexadecimal color code
                            if poly_color:

                                poly_color = re.search("PolyStyle.*PolyStyle", style_string) 
                                poly_color = re.search("<color>(.*)</color>", poly_color.group()) 
                                poly_color = poly_color.group(1)


                            # Else assign it a white default color
                            else:

                                poly_color = 'white'


    return poly_color, line_color, line_width




class Kml_Merge:

    """
    Summary:  This script combines multiple kml files into one kml. In the
    resulting merged kml, each placemark text will be prepended with the file
    name, so that placemarks with duplicate names can be differentiated from
    each other.

    'outFolder' - String. The directory where you want to save the output kml to. For
    example:

        outFolder = 'C:\Path\to\Folder'
        
    'combined_kml_name' - String. Name of the kml that all the other kmls that will be
    merged into. The combined_kml_name can end in '.kml' or it doesn't have to.
    For example:

        combined_kml_name = 'mykml' OR
        combined_kml_name = 'mykml.kml' 

    'kmls' - List. List of kml files that will be merged into one master kml
    file. For example: 

        kmls = [
                'C:\path\to\kml\mykml_2.kml',
                'C:\path\to\kml\mykml_2.kml',
                ]

    'alt_namespaces' - List. List of alternative name spaces to use when
    searching for placemarks in the kml. CAUTION! Some placemarks can have more than one
    namespace assigned to it.  This is common for kmls that were generated
    inside Google Earth.  So, if you pass in a namespace and the namespace that is 
    recognized by the regex in this script is also assigned to a particular
    placemark, then in the merged kml a placemark will be generated for
    each namespace.  For example:

        alt_namespaces = ['http://www.opengis.net/kml/2.2']

    'preserve_styling' - Optional argument that if set to '=True', then the styling
    for placemarks will be preserved. Currently, styling is not preserved for
    polylines or polygons.  Only the placemark image is preserved, not the
    scale. If this argument is not included then all the placemarks, polylines,
    polygons, etc will default to yellow pushpins and white polygons. For example,
        
        preserve_styling=True


    """


    def __init__( self, outFolder, combined_kml_name, kmls, alt_namespaces=None, preserve_styling=None, append_file_name=None ):

        self.outFolder = outFolder
        self.combined_kml_name = combined_kml_name
        self.kmls = kmls
        self.alt_namespaces = alt_namespaces
        self.preserve_styling = preserve_styling
        self.append_file_name = append_file_name


        # if file passed in ends with a '.kml' the leave it, if not then add
        # it.
        if self.combined_kml_name.endswith('.kml'):
            pass
        else:
           self.combined_kml_name = self.combined_kml_name + '.kml'


        self.outFilePath = os.path.join( self.outFolder, self.combined_kml_name ) 

        # Variable that holds the entire file in memory. I would prefer to not
        # do this, but I can't figure out how to write to a file at a specific line.  
        self.entire_File = ''

        # variable to hold all the sylting information
        self.styling_xml = ''

        # Dictionary used to genrate unique ids for stying 
        self.styling_dic = {}

        # terms which are part of the styling Url data that are used to
        # determine if the place mark is a paddle with a shape in it
        self.shape_file_handles = [ 'blank', 'diamond', 'circle', 'square', 'stars' ]

        # set that holds the variable used in the url to Google's server. Used
        # to generate the placmark icons for points.
        self.shapes_pngs = set( ['arrow-reverse', 'arrow', 'track', 'donut', 'forbidden',
                             'info-i', 'polygon', 'open-diamond', 'square',
                             'star', 'target', 'triangle', 'cross-hairs', 'placemark_square', 
                             'placemark_circle', 'shaded_dot', 'dining', 'cofee', 'bars', 
                             'snack_bar', 'man', 'woman', 'wheel_chair_accessible', 'parking_lot','cabs',
                             'bus', 'truck', 'rail', 'airports', 'ferry', 'heliport', 'subway', 'tram', 'info',
                             'info-circle', 'flag', 'rainy', 'water', 'snowflake_simple', 'marina', 'fishing',
                             'sailing', 'swimming', 'ski', 'parks', 'campfire','picnic', 'campground',
                             'ranger_station', 'toilets', 'poi', 'hiker', 'cycling', 'motorcycling', 'horsebackriding',
                             'play', 'golf', 'trail', 'shopping', 'movies', 'convenience', 'grocery', 'arts',
                             'homegardenbusiness', 'electronics', 'mechanic','gas_stations', 'realestate',
                             'salon', 'dollar', 'euro', 'yen', 'firedept', 'hospitals', 'lodging', 'phone', 'caution',
                             'earthquake', 'falling_rocks', 'post_office', 'police', 'sunny', 'partly_cloudy', 'volcano',
                             'camera', 'webcam'
                             ]) 
        

    def merge(self):
        """
        Method that does the actual merging of multiple kmls
        """

        affirmative_response = 'yes'

        print
        print 'Making master kml: ', self.outFilePath 

        # Open file for writing
        f = open( self.outFilePath , 'w' )
   
        if self.preserve_styling == None: 

            outFilePath = os.path.join( self.outFolder, self.combined_kml_name ) 

            # write the header info four our new kml( the kml that will be holding all the merged kmls)
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
                '<Document>\n'
                '<name>%s</name>\n' % self.combined_kml_name.replace('.kml','') +
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

            # for each kml in list
            for kml in self.kmls:

                # Make the current file path
                current_file = os.path.splitext( os.path.basename( kml ) )[0]

                print
                print 'Extracting placemarks from: ', current_file

                # Regex to find all the xml namespaces. 
                find_namespace = lambda l: re.findall( r'xmlns\s?=\s?.+"' , l )

                # Gets all the namespaces found in the kml file
                name_space = [ find_namespace(l)[0].split('"')[1] for l in open( kml, 'r') if len( find_namespace(l) ) > 0 ][0]

                # Parse the file
                et = etree.parse( kml )
                
                # If the alt_namespaces parameter was passed in
                if self.alt_namespaces != None:

                    Alt_namespaces = alt_namespaces 

                    # for each namespace in the list
                    for alt in Alt_namespaces:

                        # Find all the placemarks using the current namespace
                        Placemarks = et.findall('{%s}Document/{%s}Placemark' % ( alt, alt ))

                        # call the function to find the placemarks
                        find_placemarks( Placemarks, current_file, etree, f )

                        print len( Placemarks ), ' placemarks found'
                        
                # Find all the placemarks using the current namespace
                Placemarks = et.findall('{%s}Document/{%s}Placemark' % ( name_space, name_space ))
               
                if self.append_file_name == True:
                    find_placemarks( Placemarks, current_file, etree, f, append_file_name='Yes' )
                else:
                    find_placemarks( Placemarks, current_file, etree, f )

                print len( Placemarks ), ' placemarks found'


        elif self.preserve_styling == True: 

            # write the header info four our new kml( the kml that will be holding
            # all the merged kmls)
            f.write( '<?xml version="1.0" encoding="UTF-8"?>\n' + 
                     '<kml xmlns="http://www.opengis.net/kml/2.2">\n' +
                     '<Document>\n' +
                     '<name>%s.kml</name>\n' % self.combined_kml_name)
            
            # for each kml in list
            for kml in self.kmls:

                # Make the current file path
                current_file = os.path.splitext( os.path.basename( kml ) )[0]

                print
                print 'Extracting placemarks from: ', current_file

                # Regex to find all the xml namespaces. 
                find_namespace = lambda l: re.findall( r'xmlns\s?=\s?.+"' , l )

                # Gets all the namespaces found in the kml file
                name_space = [ find_namespace(l)[0].split('"')[1] for l in open( kml, 'r') if len( find_namespace(l) ) > 0 ][0]

                # Parse the file
                et = etree.parse( kml )
                
                # If the alt_namespaces parameter was passed in
                if self.alt_namespaces != None:

                    Alt_namespaces = self.alt_namespaces 

                    # for each namespace in the list
                    for alt in Alt_namespaces:

                        # Find all the placemarks using the current namespace
                        Placemarks = et.findall('{%s}Document/{%s}Placemark' % ( alt, alt ))

                        # call the function to find the placemarks
                        find_placemarks( Placemarks, current_file, etree, f, self.styling_xml )

                        print len( Placemarks ), ' placemarks found'

                        
                # Find all the placemarks using the current namespace
                Placemarks = et.findall('{%s}Document/{%s}Placemark' % ( name_space, name_space ))
                
                print len( Placemarks ), ' placemarks found'

                # for each Placemark
                for marks in Placemarks:

                    # The all the children nodes of marks
                    marks_children = marks.getchildren()

                    # Grab all the nodes, just the text
                    nodes = [ node.tag.split('}')[1] for node in marks_children ]

                    # reset the values so the previous nodes colors are not
                    # carried over the current polygon 
                    polygon_checker = ''
                    polyline_checker = ''
                    line_color = ''
                    poly_color = ''
                    line_width = ''

                    if 'Polygon' in nodes:

                        # call function to grab xml styling elements
                        poly_color, line_color, line_width = poly_checker( et, name_space, marks_children )

                        # A variable to pass along that will trigger building a <style> for polygons instead of a point
                        polygon_checker = affirmative_response

                    elif 'LineString' in nodes:

                        # call function to grab xml styling elements
                        poly_color, line_color, line_width = poly_checker( et, name_space, marks_children )

                        # A variable to pass along that will trigger building a <style> for polygons instead of a point
                        polyline_checker = affirmative_response

                    # If the child node text is 'styleUrl'
                    if 'styleUrl' in nodes:

                        if self.append_file_name == True:
                            name = [ node for node in marks_children if node.tag.split('}')[1] == 'name' ][0]
                            name.text = current_file + ' : ' + name.text 

                        child = [ node for node in marks_children if node.tag.split('}')[1] == 'styleUrl' ][0]

                        # number of pins with same basename allowed without script blowing up
                        number_of_allowed_dups = 10000

                        # Calling recursion function to genrate unique style id's
                        style = unique_name( child.text, self.styling_dic, number_of_allowed_dups ) 

                        # Making sure the node text is the same as the unique_name that was just generated
                        child.text = style

                        # Removing characters 
                        style = child.text.replace('#','')
                        style = style.replace('msn_','')
                        
                        # Variable created to see if it is a paddle with a shape in it. Has to be a try, except clause because
                        # it will blow up if it can not run the code
                        try:
                            shape_paddle_test = style.split('-')[1]
                            shape_paddle_test = re.sub( r'\d+',"", shape_paddle_test )
                        except:
                            pass

                        # Variable created to see if it is a a shape (i.e. fishing, camping, snow, etc). Has to be a try, except clause because
                        # it will blow up if it can not run the code
                        try:
                            shapes_shape_test = re.sub( r'\d+',"", style )
                        except:
                            pass


                        # If it is a push pin
                        if 'pushpin' in style and polygon_checker != affirmative_response and polyline_checker != affirmative_response:

                            # The directory to include when generating the url
                            # at Google's server
                            style_directory = 'pushpin'

                            # Removing any numbers at end so the url will have correct url
                            url_name = re.sub(r'\d+',"", style)

                            # Calling the function to generate the <Style> and
                            # <StyleMap> xml 
                            placemark_styling_xml = styling( style, url_name, style_directory, pushpin=True )
                            
                        # If it is a Polygon.  
                        elif 'pushpin' in style and polygon_checker == affirmative_response:

                            # The directory to include when generating the url
                            # at Google's server
                            style_directory = 'pushpin'

                            # Removing any numbers at end so the url will have correct url
                            url_name = re.sub(r'\d+',"", style)

                            placemark_styling_xml = styling( style, url_name, style_directory,
                                                             line_color=line_color, poly_color=poly_color,
                                                             line_width=line_width, polygon=True 
                                                            )

                        # If it is a Polyline.  
                        elif 'pushpin' in style and polyline_checker == affirmative_response:

                            # The directory to include when generating the url at Google's server
                            style_directory = 'pushpin'

                            # Removing any numbers at end so the url will have correct url
                            url_name = re.sub(r'\d+',"", style)

                            placemark_styling_xml = styling( style, url_name, style_directory, line_color=line_color, 
                                                             line_width=line_width, polyline=True 
                                                            )
                    
                        # If it is a paddle with a letter in it
                        elif style[0] in string.ascii_uppercase and len( style ) != 0:

                            # The directory to include when generating the url at Google's server
                            style_directory = 'paddle'

                            # Removing any numbers, which would be there if
                            # there were more than one placemark with the same
                            # paddle icon, at end so the url will have correct url
                            url_name = re.sub(r'\d+',"", style)

                            # Calling the function to generate the <Style> and <StyleMap> xml 
                            placemark_styling_xml = styling( style, url_name, style_directory, pushpin=True )
                           
                        # If the placemark is a paddle with a number in it
                        elif style[0] in [ str(r) for r in range(0,11)]:

                            # The directory to include when generating the url
                            # at Google's server
                            style_directory = 'paddle'

                            # Grabbing only the first index in the url_name, so
                            # we can generate the proper url for Google's
                            # server.  We can use a reg ex to remove all
                            # numbers (at least I can't figure it out) because
                            # the item we are after is a number, but at the
                            # first index
                            url_name = style[0] 

                            # Calling the function to generate the <Style> and
                            # <StyleMap> xml 
                            placemark_styling_xml = styling( style, url_name, style_directory, pushpin=True )

                        # If it is paddle with a shape in it
                        elif shape_paddle_test in self.shape_file_handles:

                            # The directory to include when generating the url at Google's server
                            style_directory = 'paddle'

                            # Removing any numbers, which would be there if
                            # there were more than one placemark with the same
                            # paddle icon, at end so the url will have correct url
                            url_name = re.sub(r'\d+',"", style)

                            # Calling the function to generate the <Style> and <StyleMap> xml 
                            placemark_styling_xml = styling( style, url_name, style_directory, pushpin=True )

                        # if it is a shape (i.e. ranger station, snow, volcano, etc)
                        elif shapes_shape_test in self.shapes_pngs:

                            # The directory to include when generating the url
                            # at Google's server
                            style_directory = 'shapes'

                            # Removing any numbers, which would be there if
                            # there were more than one placemark with the same
                            # paddle icon, at end so the url will have correct url
                            url_name = re.sub(r'\d+',"", style)

                            # Calling the function to generate the <Style> and
                            # <StyleMap> xml 
                            placemark_styling_xml = styling( style, url_name, style_directory,pushpin=True )

                          
                    # If the child node text is 'name'
                    elif 'name' in nodes:

                        if self.append_file_name == True:
                            name = [ node for node in marks_children if node.tag.split('}')[1] == 'name'   ][0]
                            # Make a new name that is formatted like:
                            # 'the_file_name' + 'the orginal node text'. This is
                            # done so we can tell what placemark the file was
                            # associated with originally. Maybe this should be an
                            # optional argument?
                            name.text =  current_file + ' : ' + name.text

                        else:
                            pass
                                         
                    # Try to add the styling information for the placemark. Has to
                    # be a try because if there was none associated with it, then
                    # the code would fail.
                    try:

                        self.styling_xml = self.styling_xml + placemark_styling_xml

                    except:
                        pass
                        
                    # Convert the placemark node to a string
                    placemark_toString = etree.tostring( marks )

                    # Removing the namespace information because there could be
                    # many different namespaces (which are strings now), and do not
                    # ( I believe ) actually act like namespaces
                    placemark_toString = re.sub(r'ns\d:', "" , placemark_toString )

                    # removing other namespace info in placemark
                    placemark_toString = re.sub(r'xmlns.+"', "" , placemark_toString )

                    # Write the placemark string to our new kml file
                    #f.write( placemark_toString )

                    # Add to string holding entire file content
                    self.entire_File = self.entire_File + placemark_toString

            # maybe it would be nice to write the data to a specific line in the
            # kml instead of having to hold it all in memory, but i don't know how
            #f.close()
            #f = open( self.outFilePath , 'wa' )
            #f.seek(6)
            #f.write( self.styling_xml )

            # Add to string holding entire file content
            self.File = self.styling_xml + self.entire_File

            # Write to file
            f.write( self.File )
            
        # Close document tags
        f.write('</Document>\n'
                '</kml>')

        # close file
        f.close()    

        print 
        print 'Kml merged successfully merged into master!'




