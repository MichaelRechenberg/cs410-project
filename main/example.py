# Author: Michael Rechenberg
#
# Example code for PSS class and PSS_Runner

from PSS import PSS
import os
import metapy

# We create a PSS_Runner object
root_dir = os.getcwd()
a = PSS.PSS_Runner(root_dir,  "config.toml")


# We set the parser mappings for each collection so every file within
#  a specific collection is parsed a different way
#
# These can be any functions we want as long as they adhere to this format:
#
# def some_parser_func(raw_filename, parsed_filename)
#     """
#         raw_filename - absolute path to the file within the raw_docs 
#             directory that we want to parse
#         parsed_filename - absolute path to where within the parsed_docs direcory
#             we should save the parsed version of our file
#     """
#
# The user can write whatever parser they want to use...PSS.py has some examples

parser_mappings = {
  'header_files': PSS.copy_parser_function,
  'mp_docs':      PSS.stupid_parse_file2,
  'angrave_book': PSS.html_parser_function,
  'pdfs':         PSS.pdf_parser_function
}
a.parser_mappings = parser_mappings

# We set weights for each collection
# These weights will be multiplied to the score given by a
#   'real' ranker like BM25/Dirichlet Prior in order to give
#   documents from one collection a higher score than documents
#   from other collections
weights = {
  'header_files': 1,
  'angrave_book': 5,
  'pdfs'        : 1,
  'mp_docs'     : 0,
}
a.weights = weights
a.parse_raw_docs()
a.generate_index()

#Oh wait, we actually want to have the mp_docs collection have
# a non-zero weight to it.  Let's update the weights.
#Note we can do this without having to generate the index again
# so we can do this on a per-query basis if we want to 
a.weights['mp_docs'] = 3

# Let's ask some queries
while(True):
  print("Enter a query")
  print("Type ! to exit\n")
  query = input()
  if(query == '!'):
    break

  #score_query returns a list of tuples laid out as such:
  # (doc_id, score, filepath_relative_to_raw_docs_directory)
  results = a.score_query(query, 10)
  print("Printing results for query:\n")
  for result in results:
    print(result)


    #Here's how we can get the raw version of the file

    #abs_raw_filename = os.path.join(a.get_raw_docs_dir(), result[2])
    #with open(abs_raw_filename, 'r') as f:
      #for x in range(10):
        #print(f.readline())

    #Here's how we can get the parsed version of the file

    #abs_parsed_filename = os.path.join(a.get_parsed_docs_dir(), result[0])
    #with open(abs_parsed_filename, 'r') as f:
    #   do_stuff_with_file(f)
  print()

