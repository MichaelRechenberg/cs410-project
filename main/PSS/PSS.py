import os
from bs4 import BeautifulSoup
# The most important package :P
import metapy


class PSS_Runner:

    #String containing the name of the directory that contains the raw, unmodified
    #  documents that the instructor wishes to provide students
    #Instructors should create single-level directories within the raw_docs directory
    #  and then designate the weights and parser functions they want applied to documents
    #  in each directory.  In comments you may see these single-level directories 
    #  referred to as 'collections'
    #The documents within raw_docs_dir will be served to students via Flask if they
    #  wish to see that documents
    raw_docs_dir = "raw_docs"
    #String containing the name of the directory where PSS_Runner will store the parsed
    #  version of every file within the raw_docs directory 
    parsed_docs_dir = "parsed_docs"
    
    def __init__(self, root_dir, config_file, weights=None, parser_mappings=None):

        #String containing the absolute path to the 'root directory' of PSS, 
        #  the directory where the raw_docs, parsed_docs, and config.toml file reside    
        self.root_dir = root_dir
        
        #List of all directories within the raw_docs directory
        #Instructors should put the files they want to provide within a single-level 
        #  directory within the raw_docs directory
        #Directory names and file names must be unique
        self.collections = os.listdir(os.path.join(self.root_dir, PSS_Runner.raw_docs_dir))
        
        #Dictionary with (collection_name, weight) key-value pairs
        #Used for determining per-collection weights to multiply a document's total score by
        self.weights = weights
        
        #Dictionary with (collection_name, parser_function) mappings
        #Used so each collection can have a specified parser for all files in that parser
        self.parser_mappings = parser_mappings 
        
        #String containing absolute path to the config.toml file 
        #  but you only have to pass in the config_file's path relative to root_dir
        #  when you pass it into PSS_Runner's constructor
        self.config_file = os.path.join(self.root_dir, config_file)
       
        #The core ranker used for ranking documents
        #This ranker will compute a score for each document and then PSS_Runner
        #  will take that score and multiply it by the collection-specific weight
        #  as defined by the 'weights' field
        self.ranker = metapy.index.OkapiBM25(k1=1.2, b = 0.75, k3=500)
        
        #This will be a metapy inverted index, generated with parse_raw_docs()
        self.idx = None 

        #The PSS ranker, the ranker that uses the 'real' ranker and then applies
        #   the collection-specific weights dictated by self.weights
        self.pss_ranker = PSS_Runner.PSS_Runner_Ranker(self)

        
        
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
            Utility function to make a text file into one long line 

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
            Parse all of the files within every collection in the raw_docs directory according
                to that collection's specified parser function, then store the parsed versions
                within the parsed_docs directory. Note each file within the parsed_docs directory
                is named by it's doc_id...if you need to recover the raw file you can access the
                raw file's relative path to the raw_docs directory by looking at the metadata of
                the PSS_Runner's inverted index.

                  e.g.

                    doc_path = self.idx.metadata(doc_id).get("doc_path")


             This function also creates and writes to 2 files that MeTA needs to operate

                  metadata.dat - the metadata file that the inverted index uses. For every file
                    within a collection, this function will write that file's relative path
                    to the raw_docs directory so you can retrieve the raw file given a doc_id

                  parsed_docs-full-corpus.txt - MeTA uses this to construct a file-corpus
                    This function writes the following line per document:

                      [none] doc_id

                    We write doc_id because each file is being named by its doc_id within parsed_docs 
                    
                     
        """
        print("Beginning Parsing")

        #parsed_docs-full-corpus.txt
        #order of files within this file determines what docID's are
        full_corpus_filename = os.path.join(self.get_parsed_docs_dir(), "{0}-full-corpus.txt".format(PSS_Runner.parsed_docs_dir))
        
        #metadata.dat file
        metadata_filename = os.path.join(self.get_parsed_docs_dir(), "metadata.dat")
       
        try: 
          # Document ID as used in MeTA and used here for naming files in the parsed_docs directory
          # We can recover the 'raw' file from using the doc_path metadata found within the index we'll
          #   generate later
          doc_id = 0
          with open(full_corpus_filename, "w+") as full_corpus_file:
              with open(metadata_filename, "w+") as metadata_file:

                  #Parse every file within the raw_docs directory
                  for collection in self.collections:
                      #Assumes all collections contain only files, no subdirectories
                      files = os.listdir(os.path.join(self.get_raw_docs_dir(), collection))
                      # Select the parser function we want to use on documents in this collection
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
                          
                          abs_parsed_filename = os.path.join(self.get_parsed_docs_dir(), str(doc_id))
                          parser_func(abs_raw_filename, abs_parsed_filename)
                          #write doc_path in the metadata.dat file 
                          relative_to_raw_docs_path = os.path.join(collection, raw_file)
                          metadata_file.write("{0}\n".format(relative_to_raw_docs_path))
                          #write doc_id entry into parsed_docs-full-corpus.txt
                          full_corpus_file.write("[none] {0}\n".format(str(doc_id)))
                          doc_id += 1

        except IOError as err:
          print("I/O Error in parse_raw_docs() {0}: {1}".format(err.errno, err.strerror))
          print("You should remove all files from parsed_docs/, replace file.toml within parsed_docs")
          print("and remove the idx/ directory created by MeTA before running again")
        else:
          print("Finished Parsing Successfully")
        
        
        
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
                A list of tuples containing the following information:
                  (doc_id, score, filepath_relative_to_raw_docs_directory)

                Returns None if the parser_mappings or weights of the PSS_Runner have not
                    been set before calling this function
        """
        if(self.parser_mappings is None):
          print("You must set the paser_mappings of the PSS_Runner before querying")
          return None
        elif(self.weights is None):
          print("You must set the  weights of the PSS_Runner before querying")
          return None
        query = metapy.index.Document()
        query.content(user_query)

        #List containing the results of the query
        result_tuples = []

        #ranked_list contains tuples of (doc_id, score)
        ranked_list = self.pss_ranker.score(self.idx, query, num_returned)
        for ranked_list_result in ranked_list:
            doc_id = ranked_list_result[0]
            doc_path = self.idx.metadata(doc_id).get("doc_path")
            result_tuples.append( (doc_id, ranked_list_result[1], doc_path) )

        return result_tuples
    

    
            

    class PSS_Runner_Ranker(metapy.index.RankingFunction):
        """
            Custom RankingFunction that applies the 'real' ranking 
                function (BM25, Dirichlet Prior) of a PSS_Runner to score a document
                and then multiplies that score by the collection-specific
                weight 
    
        """
        def __init__(self, pss_runner):
            """
                pss_runner - the PSS_Runner object that contains this PSS_Runner_Ranker
            """
            self.pss_runner = pss_runner
            super(PSS_Runner.PSS_Runner_Ranker, self).__init__()
    
        def score_one(self, sd):
            #Score the document based off of the 'real' ranker
            #  that the containing PSS_Runner is using
            raw_score = self.pss_runner.ranker.score_one(sd)
            doc_id = sd.d_id
            #fetch this documents filepath, relative to the raw_docs directory
            doc_path = self.pss_runner.idx.metadata(doc_id).get("doc_path")
            collection_name = os.path.dirname(doc_path)
            #apply the collection-specific weight
            weight = self.pss_runner.weights[collection_name]
            return raw_score * weight




# example parsers
# all parsers take the same form 
#
#  def some_parser_function(raw_filename, parsed_filename):
#
#            raw_filename -- the absolute path to the file within raw_docs we want to parse
#            parsed_filename -- asbolute path of where within the parsed_docs directory we will
#                store the parsed version of the file
#   
def stupid_parse_file(raw_filename, parsed_filename):
    """
        Params:
            raw_filename -- the absolute path to the file within raw_docs we want to parse
            parsed_filename -- asbolute path of where within the parsed_docs directory we will
                store the parsed version of the file

        Dummy parser which just adds RITA RITA RITA as the last line
            and writes the parsed file to parsed_docs_directory
    """

    with open(raw_filename, "r") as raw_file:
        with open(parsed_filename, "w+") as parsed_file:
            parsed_file.write('RITA RITA RITA\n')
            for line in raw_file:
                parsed_file.write(line)
            parsed_file.write('RITA RITA RITA\n')
        
    
def stupid_parse_file2(raw_filename, parsed_filename):
    """
        Params:
            raw_filename -- the absolute path to the file within raw_docs we want to parse
            parsed_filename -- asbolute path of where we will store the parsed file within
                the parsed_docs directory

        Dummy parser which just adds MP MP MP to the first and last line
    """

    with open(raw_filename, "r") as raw_file:
        with open(parsed_filename, "w+") as parsed_file:
            parsed_file.write('MP MP MP MP\n')
            for line in raw_file:
                parsed_file.write(line)
            parsed_file.write('MP MP MP MP\n')
            
            
#Some not so dumb example parsers

def copy_parser_function(raw_filename, parsed_filename):
    """
        Simple parser function that simply copies the file to the parsed_docs directory,
            unmodified
        If you want to not modify the raw file at all, use this function
        Copying line by line and not shutil.copyfile() because we don't want to lose metadata
    """
    with open(raw_filename, "r") as raw_file:
        with open(parsed_filename, "w+") as parsed_file:
            for line in raw_file:
                parsed_file.write(line)

def html_parser_function(raw_filename, parsed_filename):
    """
        HTML parser function that extracts the text from certain tags
            (using Beautiful Soup) and writes the text from each tag on
            it's own line
    """
    tags = ['p', 'h1', 'h2', 'h3', 'title']
    with open(raw_filename, "r") as htmlfile:
        soup = BeautifulSoup(htmlfile, "html5lib")
        with open(parsed_filename, "w+") as parsed_file:
            for tag in tags:
                found_tags = soup.find_all(tag)
                for found_tag in found_tags:
                    parsed_file.write("{0}\n".format(found_tag.text))

                    
def pdf_parser_function(raw_filename, parsed_filename):
        
    #If the user isn't on a linux machine or pdftotext isn't installed they'll have to to generate
    #  the text representation via some external mechanism and store
    #  that representation within the parsed_docs directory
    #The metadata information and parsed_docs-full-corpus.txt will still be filled
    #  out correctly if the user adds their processed PDF into the parsed_docs
    #  directory without modifying the file's name
    
    print("Note: PSS_Runner's PDF Parser requires the pdftotext program for Linux")
    # Use pdftotext command, so this only works on linux
    os.system("pdftotext {0} {1}".format(raw_filename, parsed_filename))


def pptx_parser_function(raw_filename, parsed_filename):
    print("No pptx parser yet :/")


            
