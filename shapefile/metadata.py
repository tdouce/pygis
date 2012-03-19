import re, os, inspect, types
import xml.etree.cElementTree as etree
from xml.parsers.expat import*

class Get_Esri_Metadata:


    def __init__(self, shapeFilePath):

        self.tree = etree.parse( shapeFilePath )


    def __getBase( self, x_path, x_path_children  ):

        self.results = []
        self.x_path_root = x_path
        self.x_path_children = x_path_children

        finds = self.tree.findall( self.x_path_root )

        for each in finds:

            tempcont = []

            for each_1 in each.getchildren():

                if each_1.tag in self.x_path_children:

                    tempcont.append( each_1.text )

            self.results.append( tempcont )

       
        if len( self.results ) > 1:
        
            self.count = len( self.results )

        else:

            
            if len( self.results ) == 1: 

                self.results = self.results[0][0]

                self.count = len( [ self.results ] )

            else:

                self.results = self.results[0][0]

                self.count = len( self.results )



    def attributes( self ):

        x_path = "eainfo/detailed/attr"       

        children = ['attrlabl','attrtype','attwidth','atnumdec']

        self.__getBase( x_path, children )


    def featureCount( self ):

        x_path = "eainfo/detailed/enttyp"

        x_path_children = [ "enttypc" ]

        self.__getBase( x_path, x_path_children )

    
    def geomType( self ):

        x_path = "spdoinfo/ptvctinf/esriterm"

        children = [ "efeageom" ]

        self.__getBase( x_path, children )


    def boundBox( self ):

        x_path = "idinfo/spdom/bounding"

        children = [ "westbc","eastbc","northbc","southbc" ]

        self.__getBase( x_path, children )



class Write_Metadata:


    '''
    Summary: This class updates the ESRI xml metadata file with information
    passed in.  Each method (apart from the private methods) has a hard coded
    Xpath to the node to be populated.  This class builds the xml node path if
    it does NOT exist and if the node path does exists, then it only populates
    the node of interest.  There are two private methods.
    '_updateNode_SingleChild' is used to update a node if it is only one level
    deep in the node tree and a node that occurs only once.  The other private method
    '_updateNode_MultipleChildren' updates nodes that are two levels deep and
    for nodes that occure more than once. They
    both require unique logic.  Every other method in this class invokes one of
    the two private methods to update the node of interest by passing in unique
    text and a unique xpath.  The xpath is hard coded into each of the methods
    because (supposedly) these paths should not change.  If ESRI changes the
    node placement then these xpaths will need updating.  
    '''
    
    def __init__(self, pathToShapeFile):

        '''
        Summary: This method occurs on instantiation of the object. It takes an xml file
        and reads all the contents to memory and converts it to a string for
        editing.  This method takes one argument.
        
        'pathToShapeFile' - The path to the shapefile you want updated, and
        implicitly the xml file you want updated.

        '''

        self.pathToShapeFile = pathToShapeFile

        # Open original xml file
        xmlDoc = open( self.pathToShapeFile ,'r')

        # Read to lines
        xml_lines = xmlDoc.read()

        # close it
        xmlDoc.close()

        # variable that holds all the xml as a string
        self.root = etree.fromstring( xml_lines )

       
    
    def __updateNode_SingleChild(self, custom_text, x_path ):

        '''
        Summary: This method 1) updates the text in a node if it exists and 2) if it does not
        exist, then it checks whether or not each node in the Xpath exists or not.  
        If it does NOT exist, then it creates it.  It then puts adds the
        'custom_text' to the last node in the xPath. This method is different than the
        method 'updateNode_MultipleChildren' in that it only creates one child per
        parent node, while the 'updateNode_MultipleChildren' method removes multiple
        children from a node and then adds multiple children to a node. Example
        for this method:

        'xPath' - This argument is the xpath to the node that is to be updated.
        For example: idinfo/abstract"
        
        'custom_text' - This is the text that is to be included in the node.
        For example: 'This is an abstract'


        This following is an example of how this method works given the
        arguments above:

        original xml document:

        <idinfo>
        </idinfo>

        This method looks at the xPath that is passed in and checks to see if
        every node in the xPath exists or not.  If a node does not exist it will
        create the node and if it does exist it will move on to the next node
        in the xPath.  It does this for every node in the xPath.

        Considering the above example above.  This method will check if the
        <idinfo> node exists. If it does not exist then it will create it.  In this
        case, it does not need to create the <idinfo> node. It then checks
        whether or not the <abstract> node exisits.  In this case, it does not
        exist so the <abstract> node is created. It then adds the 'custom_text' to
        the last node in the xPath. So, it ends up like:
        
        <idinfo>
            <abstract> This is an abstract </abstract>
        </idinfo>

        If the <abstract> node already exsisted, it would only replace the text
        in the <abstract> node.

        '''

        self.custom_text = custom_text
        self.x_path = x_path


        ####### BEGIN: Checking if child of root node exists
        # For shapefiles that are dynamically generated by a script the the
        # first node in the x_path will probably not exist.  This bit of code
        # checks if the this node exists, and if it doesn't then it builds it.
        # This is different than the code below that dynamiclly generates the
        # xpaths because this uses the root node which requires a little
        # different syntax.  This could have been added below, but the code is
        # already nested multiple times and this makes it a little clearer.
        # This is the first node in the xpath.
        firstNode = self.x_path.split('/')[0]

        # Find the text associated with with the xpath
        firstNode_text = self.root.findtext( firstNode )


        if firstNode_text == None:

                # create the node and add text to it. 
                etree.SubElement( self.root , firstNode )


        ##### END: Checking if child of root node exists

        
        # This is the last node in the xpath.
        nameOfNodeToAdd = self.x_path.split('/')[-1:][0]

        # Find the text associated with with the xpath
        org_text = self.root.findtext( self.x_path )
        
        # if there is no text associated with the node in the xPath, then the node 
        # does NOT exist, then build it node by node
        if org_text == None:

            nodes = self.x_path.split('/')

            for node in nodes:

                index = nodes.index( node )

                build_xPath = []
                
                for each in range( index + 1 ):

                    build_xPath.append( nodes[ each ] )

                findtext_xPath = '/'.join( build_xPath )

                # If the <timeperd> node does not exist, then build it
                if self.root.findtext( findtext_xPath  ) == None:

                    # Make an object out of the parent node you want to add a child to. 
                    # This path does NOT navigate to the actual node you want to
                    # add, but rather to the parent node you want to add

                    # split the xpath 
                    findtext_xPath_split = findtext_xPath.split('/')

                    # Remove the last item
                    del findtext_xPath_split[-1:]

                    # Join the list together => give you the xpath to the
                    # parent node you want to add a child to
                    parentNode = '/'.join( findtext_xPath_split )

                    # if the last node in the xpath (nameOfNodeToAdd) is the
                    # same as the node (the current item that is being iterated
                    # over) that is being iterated over, then it is the last node in
                    # the hierarchy of nodes and it is the node that should
                    # have text in it. 
                    if nameOfNodeToAdd == node:

                        # Make an object of the node parent node you want to add
                        nodeToAdd = self.root.find( parentNode )

                        # create the node and add text to it. 
                        etree.SubElement( nodeToAdd , node ).text = self.custom_text


                    # If the node that is being iterated over does NOT equal
                    # the last node in the heirarchy, then make the node
                    # (without adding text to it)
                    else:

                        nodeToAdd = self.root.find( parentNode )

                        # create the node. This creates the <place></place> node
                        etree.SubElement( nodeToAdd , node )

                else:

                    pass

        # If the <timeperd> node does exist, leave it alone
        else:

            # Finds the node to edit 
            nodeToEdit = self.root.find( self.x_path )

            # Changes the text in the node
            nodeToEdit.text = self.custom_text


            
    def __updateNode_MultipleChildren( self, custom_text, x_path ):

        '''
        Summary: This method is different from 'updateNode_SingleChild' in that there are can be
        multiple children for a single node. For example:

        xPath: 'idinfo/keyword/theme/themekey'
        custom_text: ['keyword 1 text', 'keyword 2 text', 'keyword 3 text']

        xml:

        <keyword>
            <theme>
                <themekt> Some key word thesaurus wordhere </themkt>
                <themekey> an existing key word here </themekey>
                <themekey> another exsiting key word here </themekey>
            </theme>
        </keyword>

        This method updates a node that can have multiple children 
        For instance, in the above xml the <theme> node can
        have multple children nodes named <themekey> and <themekt>.  In this case we are
        updating the <themekey> nodes (see the xPath we are passing in). 
        So the problem is that we need  get rid of all the exisiting <themekey> nodes,
        while not getting rid of the <themekt> node, ie leaving them alone.  After we git 
        rid of all the <themekey> nodes we then need to create a <themekey> node for each
        item that is in the list we are passing in.

        This method is similar to 'updateNode_SingleChild' in that it checks
        whether or not every node in the xPath exsists.  If it does not exist,
        then it will create it and then move on to the next node in the xPath
        and do the same.

        Considering the xml above, the method would return

        <keyword>
            <theme>
                <themekt> Some key word thesaurus wordhere </themkt>
                <themekey> keyword 1 text</themekey>
                <themekey> keyword 2 text </themekey>
                <themekey> keyword 3 text </themekey>
            </theme>
        </keyword>


        '''

        self.custom_text = custom_text
        self.x_path = x_path

        # This is the last node in the xpath.
        nameOfNodeToAdd = self.x_path.split('/')[-1:][0]

        #######
        # Selectively removing the chid nodes

        # Splitting the x_path and getting all but the last item in the list
        ParentOfRemove = x_path.split('/')[0:-1]

        # Joing all but the last element in the xpath list to create a new xpath
        ParentOfRemove = '/'.join(ParentOfRemove)

        # This the parent of the nodes you want to remove
        ParentOfRemove = self.root.find( ParentOfRemove )

        # If the ParentOfRemove is not empty, ie there IS a node there
        if ParentOfRemove != None:

            # Get the children of the the parent node
            for child in ParentOfRemove.getchildren():

                # if the child.tag (node name) is equal to what we want to remove,
                # then remove it
                if child.tag == nameOfNodeToAdd: 

                    # you have to make an object out of the child node
                    toRemove = self.root.find( x_path )

                    # Then use the parent object and pass in the child object
                    ParentOfRemove.remove( toRemove )

                # If the child.tag is not what we want to remove then do not remove it
                else:

                    #print 'not a %s node' % nameOfNodeToAdd
                    pass


        # Find the text associated with with the xpath
        org_text = self.root.findtext( self.x_path )

        # if there is no text associated with the node in the xPath, then the node 
        # does NOT exist, then build it node by node
        if org_text == None:

            # Create a list of the xPath
            nodes = self.x_path.split('/')

            # For each node in the xPath
            for node in nodes:

                # Get the index of the node
                index = nodes.index( node )

                # List to hold the items that will be used to build the xPaths
                build_xPath = []
                
                # Building the xPath for each node
                for each in range( index + 1 ):

                    build_xPath.append( nodes[ each ] )

                # Join list to create the new xPath
                findtext_xPath = '/'.join( build_xPath )

                # If the  node does not exist, then build it
                if self.root.findtext( findtext_xPath  ) == None:

                    # Make an object out of the parent node you want to add a child to. 
                    # This path does NOT navigate to the actual node you want to
                    # add, but rather to the parent node you want to add

                    # split the xpath 
                    findtext_xPath_split = findtext_xPath.split('/')

                    # Remove the last item
                    del findtext_xPath_split[-1:]

                    # Join the list together => give you the xpath to the
                    # parent node you want to add a child to
                    parentNode = '/'.join( findtext_xPath_split )

                    # if the last node in the xpath (nameOfNodeToAdd) is the
                    # same as the node (the current item that is being iterated
                    # over) that is being iterated over, then it is the last node in
                    # the hierarchy of nodes and it is the node that should
                    # have text in it. 
                    if nameOfNodeToAdd == node:

                        # For each item in the custum_text list we are going to
                        # make the associated node tree
                        for item in self.custom_text:

                            # Make an object of the node parent node you want to
                            nodeToAdd = self.root.find( parentNode )

                            # create the node and add text to it. 
                            etree.SubElement( nodeToAdd , node ).text = item 

                    # If the node that is being iterated over does NOT equal
                    # the last node in the heirarchy, then make the node
                    # (without adding text to it)
                    else:

                        nodeToAdd = self.root.find( parentNode )

                        # create the node. This creates the <place></place> node
                        etree.SubElement( nodeToAdd , node )

                else:

                    #print '%s node already exists' % node
                    pass


        # If the <timeperd> node does exist, leave it alone
        else:

            #print '%s node DOES exist' % nameOfNodeToAdd
            pass

    
    
    def abstract(self, custom_text ):

        '''
        A brief narrative summary of the data set
        '''

        # xPath to node
        x_path = "idinfo/descript/abstract"

        self.__updateNode_SingleChild( custom_text, x_path )

    def purpose(self, custom_text ):

        '''
        A summary of the intentions with which the data set was developed.
        '''

        # xPath to node
        x_path = "idinfo/descript/purpose"

        self.__updateNode_SingleChild( custom_text, x_path )
 


    def supplementalInfo(self, custom_text ):

        '''
        There is no ESRI supplemental boiler plate text.
        '''

        # xPath to node
        x_path = "idinfo/descript/supplinf"

        self.__updateNode_SingleChild( custom_text, x_path )


    def orgNameWhoCreatedData(self, custom_text ):

        '''
        The name of an organization or individual that developed the data set.
        '''

        # xPath to node
        x_path = "idinfo/citation/citeinfo/origin"
    
        self.__updateNode_SingleChild( custom_text, x_path )


    def publicationDate(self, custom_text ):

        '''
        The date when the data set is published or otherwise made available for release
        '''

        x_path = "idinfo/citation/citeinfo/pubdate"

        self.__updateNode_SingleChild( custom_text, x_path )


    def status_progress(self, custom_text ):

        '''
        The basis on which the time period of content information is determined
        '''

        ###### General Xpath
        # xPath to node
        x_path = "idinfo/status/progress"
  
        self.__updateNode_SingleChild( custom_text, x_path )

        
    def status_update(self, custom_text ):

        '''
        The frequency with which changes and additions are made to the data set after the initial data set is completed
        '''

        # xPath to node
        x_path = "idinfo/status/update"

        self.__updateNode_SingleChild( custom_text, x_path )


    def timeperiod_caldate(self, custom_text ):

        '''
        The year (and optionally month, or month and day) for which the data set corresponds to the ground
        '''

        # xPath to node
        x_path = "idinfo/timeperd/timeinfo/sngdate/caldate"

        self.__updateNode_SingleChild( custom_text, x_path )



    def keyword_theme(self, custom_text ):

        x_path = "idinfo/keywords/theme/themekey"

        self.__updateNode_MultipleChildren( custom_text, x_path )


    def keyword_place(self, custom_text ):

        """
        Summary: This is a list of of keyword places you want to be in the metadata.
        """

        # xPath to place node
        x_path = "idinfo/keywords/place/placekey"

        self.__updateNode_MultipleChildren( custom_text, x_path )

    
    def dataUseRestrictions(self, custom_text ):

        '''
        Reference to a formally registered thesaurus or a similar authoritative source of theme keywords.
        '''

        # xPath to node
        x_path = "idinfo/useconst"

        self.__updateNode_SingleChild( custom_text, x_path )

    
    def metaDataContact_Org(self, custom_text ):

        '''
        The organization responsible for the metadata information.
        '''

        # xPath to place node
        x_path = "metainfo/metc/cntinfo/cntorgp/cntorg"

        self.__updateNode_SingleChild( custom_text, x_path )


    def metaDataContact_Addr(self, custom_text ):

        '''
        The organization responsible for the metadata information.
        '''

        # xPath to node
        x_path = "metainfo/metc/cntinfo/cntaddr/addrtype"

        self.__updateNode_SingleChild( custom_text, x_path )


    def metaDataContact_City(self, custom_text ):

        '''
        The city of the address.
        '''

        # xPath to node
        x_path = "metainfo/metc/cntinfo/cntaddr/city"

        self.__updateNode_SingleChild( custom_text, x_path )


    def metaDataContact_State(self, custom_text ):

        '''
        REQUIRED: The state or province of the address.
        '''

        # xPath to node
        x_path = "metainfo/metc/cntinfo/cntaddr/state"

        self.__updateNode_SingleChild( custom_text, x_path )


    def metaDataContact_Postal(self, custom_text ):

        '''
        The ZIP or other postal code of the address.
        '''

        # xPath to node
        x_path = "metainfo/metc/cntinfo/cntaddr/postal"

        self.__updateNode_SingleChild( custom_text, x_path )


    def metaDataContact_PhoneNum(self, custom_text ):

        '''
        The telephone number by which individuals can speak to the organization or individual.
        '''

        # xPath to node
        x_path = "metainfo/metc/cntinfo/cntvoice"

        self.__updateNode_SingleChild( custom_text, x_path )

    def metaDataContact_Email(self, custom_text ):

        '''
        The telephone number by which individuals can speak to the organization or individual.
        '''

        # xPath to node
        x_path = "metainfo/metc/cntinfo/cntemail"

        self.__updateNode_SingleChild( custom_text, x_path )

    def printIt(self):

        print etree.tostring(self.root)


    def writeToFile(self):

        writeFile = open( self.pathToShapeFile, 'w')
        writeFile.write(etree.tostring(self.root))
        writeFile.close()



def make_shapefile_metadata( xmlFilePath, dictionary ):

    '''
    Summary:  This function takes an xml file and a dictionary and populates an
    Esri metadata xml file by using the 'Esri_Metadata' class and using 
    'inspect' to dynamically call all the methods of the 'Esri_Metadata' class
    (i.e. abstract, purpose, etc) that appears in the keys of the dictionary.  
    It is used to populate the xml file for Esri shapefiles.  This is a helper 
    function that can be used in the 'csv_to_shapefile' class, 
    'OneShapefile_ManyPoints_FromDatabase' class, or any other class that creates 
    ESRI shapfiles. To use it add a method, such as 'xml' and call this function.

    'xmlFilePath' - The path the xml file you want to augment

    'dictionary' - The dictionary that is passed in containing the information
    that you want added to the ESRI xml file.  The keys of the dictionary have
    to correspond to the 'Esri_Metadata' class's methods.

    Output is a populated xml file that is compatible withe ESRI metadata
    schema and is viewable in ESRI ArcCatalog.

    '''

    # If the dictionary is empty then no action is taken.
    if dictionary == {}:

        print "No Metadata in 'metadataDict'. See if data was retrieved from database properly."

    # If dictionary is filled out
    else:

        # Make an instance using the Esri_Metadata class from pygis.shapefile.metadata 
        instance = Write_Metadata( xmlFilePath )

        # Iterationa that gets the name and method for the the instance that is
        # passed in.  In this case, the instance is of the 'Esri_Metadata'
        # class. 'Inspect.getmembers' retrieves all the methods that are bound
        # (and therefore callable) for the instance.
        for name, method in inspect.getmembers( instance, inspect.ismethod ):

            # This ensures that any private method in the 'Esri_Metadata' class
            # isn't called. If they were, they script would blow up. Private
            # methods and the '__init__' method begin with at least one '_'.
            if '_' == name[0]:

                pass

            # If the method is NOT a '__init__' or private method
            else:

                # If the name of the method is in the dictionary that was
                # passed in.  This is useful because the user can define in the
                # dictionary what xml nodes (i.e. the dictionary key. Note, the
                # keys HAVE to be spelled exactly the same as the
                # 'Esri_Metadata's class's methods) he/she wants to be
                # populated in the ESRI metadata file. So, if the name is in
                # the dictionary key, then the dictionary value is passed into the method.
                if name in dictionary:

                    method( dictionary[ name ] )


        print "Writing metadata file"

        # Calling the 'writeToFile' method of the 'Esri_Metadata' class.  This
        # writes the added data to the xml file.
        instance.writeToFile()




