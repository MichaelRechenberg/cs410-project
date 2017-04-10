import os
from bs4 import BeautifulSoup
# The most important package :P
import metapy



class PSS_Runner:
    raw_docs_dir = "raw_docs"
    parsed_docs_dir = "parsed_docs"
    
    def __init__(self, root_dir, config_file, collections=None, weights={}, parser_mappings={}):
    
        self.root_dir = root_dir
        
        #List of all directories within raw_docs_dir
        if(collections is None):
            self.collections = os.listdir(os.path.join(self.root_dir, PSS_Runner.raw_docs_dir))
        else:
            self.collections = collections
        
        #Dictionary with (collection_name, weight) key-value pairs
        self.weights = weights
        
        #Dictionary with (collection_name, parser_function) mappings
        #Used so each collection can have a specified parser for all files in that parser
        self.parser_mappings = {}
        
        #String containing asbolute path to the config.toml file
        self.config_file = config_file
        
        #TODO: allow user to modify their ranker
        self.ranker = metapy.index.OkapiBM25(k1=1.2, b = 0.75, k3=500)
        
        #This will be generated with parse_raw_docs()
        self.idx = None 
        
    def set_parser_mappings(self, mappings):
        """
            Set the parser mappings 
        """
        self.parser_mappings = mappings
    
    def set_weights(self, weights):
        """
            Sets the weights for each collection
        """
        self.weights = weights
    
        
    def get_raw_docs_dir(self):
        """
            Returns absolute path to the raw_docs directory
        """
        return os.path.join(self.root_dir, PSS_Runner.raw_docs_dir)
    
    def get_parsed_docs_dir(self):
        """
            Returns absolute path to the parsed_docs directory
        """
        return os.path.join(self.root_dir, PSS_Runner.parsed_docs_dir)

    def _make_one_line(self, parsed_file):
        """
            Makes a file into one line, separated by spaces
            Note this destroys the original parsed file
            
            Params: 
                parsed_file - absolute path to the file within parsed_docs_dir we want to 
                    make into one line
        """
        one_line = ""
        with open(parsed_file, "r") as file:
            one_line = " ".join([line.strip() for line in file])
        
        os.remove(parsed_file)
        
        with open(parsed_file, "w+") as file:
            file.write(one_line + '\n')
    
    def parse_raw_docs(self):
        """
            Parse all of the raw docs, put them in the parsed_docs_dir, 
                and fill out the metadata.dat file with the file paths as well as
                the parsed_docs-full-corpus.txt with 
                    [none] relative_filename
                blocks
        """
        print("Beginning Parsing")

        #parsed_docs-full-corpus.txt
        #order in this file determines what docID's are
        full_corpus_filename = os.path.join(self.get_parsed_docs_dir(), "{0}-full-corpus.txt".format(PSS_Runner.parsed_docs_dir))
        
        #metadata.dat file
        metadata_filename = os.path.join(self.get_parsed_docs_dir(), "metadata.dat")
        
        with open(full_corpus_filename, "w+") as full_corpus_file:
            with open(metadata_filename, "w+") as metadata_file:

                for collection in self.collections:
                    files = [f for f in os.listdir(os.path.join(self.get_raw_docs_dir(), collection))]
                    # Select the parser fucntion for this collection
                    parser_func = self.parser_mappings[collection]
                    for raw_file in files:
                        abs_raw_filename = os.path.join(os.path.join(self.get_raw_docs_dir(), collection), 
                                                        raw_file)
                        #user defined parser function that will write whatever
                        #  text representation they want into the PSS_Runner.parsed_docs_dir
                        #note that the name of the file written to PSS_Runner.parse_docs_dir
                        #  must be the same as the file that lives in PSS_Runner.raw_docs_dir
                        #  (for .pdf you should still write the_file.pdf as the file name
                        #   within PSS_Runner.raw_docs_dir even though the parsed file isn't 
                        #   actually a .pdf file...metapy treats it all like a text document)
                        parser_func(abs_raw_filename, self.get_parsed_docs_dir())
                        #write entry in metadata file
                        relative_to_public_doc_path = os.path.join(collection, raw_file)
                        metadata_file.write("{0}\n".format(relative_to_public_doc_path))
                        full_corpus_file.write("[none] {0}\n".format(raw_file))
                        #self._make_one_line(os.path.join(self.get_parsed_docs_dir(), raw_file))

        print("Finished Parsing")
        
        
        
    def generate_index(self):
        """
            Generate index based off the files in parsed_docs folder
            Call parse_raw_docs() before calling this function
        """
        self.idx = metapy.index.make_inverted_index(self.config_file)
        
    
    def score_query(self, user_query, num_returned):
        """
            Ranks all documents within the PSS_Runner's inverted index and
                weights scores wrt the collection weights
                
            user_query - string containing the query you want to search the index with
            num_returned - integer representing how many results you want returned
                Note: you may have less than num_returned results returned
                
            Returns:
                A list of document paths (relative to their location in the raw_docs directory)
                    of the top num_returned documents
        """
        query = metapy.index.Document()
        query.content(user_query)
        # Init our PSS_Runner_Ranker so we can apply the collection weights
        pss_ranker = PSS_Runner_Ranker(self)
        results = pss_ranker.score(self.idx, query, num_returned)
        top_doc_paths = []
        for result in results:
            top_doc_paths.append(self.idx.metadata(result[0]).get("doc_path"))
        return top_doc_paths
    

    
            

class PSS_Runner_Ranker(metapy.index.RankingFunction):
    """
        Custom RankingFunction that applies a typical ranking 
            function (BM25, Dirichlet Prior) to score a document
            and then multiplies that score by the collection
            weight of the document
    """
    def __init__(self, pss_object):
        """
            pss_object - the PSS_Runner object with its index and weights initialized
        """
        self.pss_object = pss_object
        super(PSS_Runner_Ranker, self).__init__()

    def score_one(self, sd):
        # Score given by a 'real' ranker
        # TODO: have this ranker passed in from PSS_Runner class
        ranker = metapy.index.OkapiBM25()
        raw_score = ranker.score_one(sd)
        doc_id = sd.d_id
        doc_path = self.pss_object.idx.metadata(doc_id).get("doc_path")
        collection_name = os.path.dirname(doc_path)
        weight = self.pss_object.weights[collection_name]
        return raw_score * weight

   
# example dumb parsers we can use
# all parsers take the form parser(filename, parsed_docs_directory)
#   filename - absolute filename of a file within the raw_docs directory
#      Note: you can extract the base filename with os.path.basename(filename)
#   parsed_docs_directory - absolute path of directory used to store the parsed docs
def stupid_parse_file(filename, parsed_docs_directory):
    """
        Params:
            filename -- the absolute path to the file within raw_docs we want to parse
            parsed_docs_directory -- asbolute path of the directory where we will store the parsed docs

        Dummy parser which just adds RITA RITA RITA as the last line
            and writes the parsed file to parsed_docs_directory
    """

    with open(filename, "r") as raw_file:
        parsed_filename = os.path.join(parsed_docs_directory, os.path.basename(filename))
        with open(parsed_filename, "w+") as parsed_file:
            parsed_file.write('RITA RITA RITA\n')
            for line in raw_file:
                parsed_file.write(line)
            parsed_file.write('RITA RITA RITA\n')
        
    
def stupid_parse_file2(filename, parsed_docs_directory):
    """
        Params:
            filename -- the absolute path to the file within raw_docs we want to parse
            parsed_docs_directory -- asbolute path of the directory where we will store the parsed docs

        Dummy parser which just adds MP MP MP as the last line
            and writes the parsed file to parsed_docs_directory
    """

    with open(filename, "r") as raw_file:
        parsed_filename = os.path.join(parsed_docs_directory, os.path.basename(filename))
        with open(parsed_filename, "w+") as parsed_file:
            parsed_file.write('MP MP MP MP\n')
            for line in raw_file:
                parsed_file.write(line)
            parsed_file.write('MP MP MP MP\n')
            
            
#Some not so dumb example parsers

def copy_parser_function(filename, parsed_docs_directory):
    """
        Simple parser function that simply copies the file to the parsed_docs directory,
            unmodified
        If you want to not modify the raw file at all, use this function
        Using line by line and not shutil.copyfile() because we don't want to lose metadata
    """
    with open(filename, "r") as raw_file:
        parsed_filename = os.path.join(parsed_docs_directory, os.path.basename(filename))
        with open(parsed_filename, "w+") as parsed_file:
            for line in raw_file:
                parsed_file.write(line)

def html_parser_function(filename, parsed_docs_directory):
    """
        HTML parser function that extracts the text from certain tags
            (using Beautiful Soup) and writes the text fro each tag on
            it's own line
    """
    tags = ['p', 'h1', 'h2', 'h3', 'title']
    with open(filename, "r") as htmlfile:
        soup = BeautifulSoup(htmlfile, "html5lib")
        parsed_filename = os.path.join(parsed_docs_directory, os.path.basename(filename))
        with open(parsed_filename, "w+") as parsed_file:
            for tag in tags:
                found_tags = soup.find_all(tag)
                for found_tag in found_tags:
                    parsed_file.write("{0}\n".format(found_tag.text))
                    
def pdf_parser_function(filename, parsed_docs_directory):
        
    #If the user isn't on a linux machine or pdftotext isn't installed they'll have to to generate
    #  the text representation via some external mechanism and store
    #  that representation within the parsed_docs directory
    #The metadata information and parsed_docs-full-corpus.txt will still be filled
    #  out correctly if the user adds their processed PDF into the parsed_docs
    #  directory without modifying the file's name
    
    parsed_filename = os.path.join(parsed_docs_directory, os.path.basename(filename))
    print("Note: PSS_Runner's PDF Parser requires the pdftotext program for Linux")
    # Use pdftotext command, so this only works on linux
    os.system("pdftotext {0} {1}".format(filename, parsed_filename))


def pptx_parser_function(filename, parsed_docs_directory):
    print("No pptx parser yet :/")


            
