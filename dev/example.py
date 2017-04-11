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
# def some_parser_func(raw_file_name, parsed_docs_directory)
#     """
#         raw_file_name - absolute path to the file within the raw_docs 
#             directory that we want to parse
#         parsed_docs_directory - absolute path to the parsed_docs directory
#     """
#
#     This function will write some representation of the file raw_file_name
#       into the parsed_docs_directory using the basename of raw_file_name
#   
#     e.g.
#     parsed_filename = os.path.join(parsed_docs_directory, os.path.basename(filename)

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
  results = a.score_query(query, 10)
  print("Printing results for query:\n")
  for result in results:
    print(result)
  print()

