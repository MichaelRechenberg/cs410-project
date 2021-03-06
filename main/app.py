from flask import Flask, render_template, request, url_for, send_from_directory
import os
import socket
import copy
from google import search
import metapy
import re


from PSS import PSS

#Global variable to the PSS_Runner 
pss = None 

#Maximum number of results we want to return to the user
MAX_NUM_RESULTS = 10
#Maximum number of google results we will search for
MAX_GOOGLE_RESULTS = 10

RAW_DOCS_DIRECTORY = PSS.PSS_Runner.raw_docs_dir

if os.name != "nt":
    import fcntl
    import struct

    def get_interface_ip(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s',
                                ifname[:15]))[20:24])

def get_lan_ip():
    ip = socket.gethostbyname(socket.gethostname())
    if ip.startswith("127.") and os.name != "nt":
        interfaces = [
            "eth0",
            "eth1",
            "eth2",
            "wlan0",
            "wlan1",
            "wifi0",
            "ath0",
            "ath1",
            "ppp0",
            ]
        for ifname in interfaces:
            try:
                ip = get_interface_ip(ifname)
                break
            except IOError:
                pass
    return ip

app = Flask(__name__)

@app.route('/')
def main():
  collections = pss.collections
  topics = []
  for elem in collections:
    obj = {}
    obj['name'] = elem
    obj['weight'] = pss.weights[elem]
    topics.append(obj)
  
  return render_template('query.html', topics = topics)

@app.route('/result', methods = ['POST'])
def handler():
  #set up user defined weights
  collections = pss.collections
  orig_weights = copy.deepcopy(pss.weights)
  for elem in collections:
    weight_req = 'weight_' + elem
    pss.weights[elem] = float(request.form[weight_req])

  query = request.form['query']

  #Use the PSS_Runner to score the query
  results = pss.score_query(query, MAX_NUM_RESULTS)
  
  pss.weights = orig_weights

  windows = []
  raw_paths = []
  file_names = []

  #run through result tuples and create a list of wots using the filepaths
  for elem in results:
    window = generate_wot(query, os.path.join(pss.get_parsed_docs_dir(), str(elem[0])))
    windows.append(window)
    raw_paths.append(os.path.join('raw_docs', str(elem[2])))
    file_names.append(os.path.basename(elem[2]))
    
  google_results = []
  for url in search(query, stop = MAX_GOOGLE_RESULTS):
    google_results.append(url)

  return render_template('result.html', 
      query = query, 
      windows = windows, 
      raw_paths = raw_paths, 
      file_names = file_names, 
      google_results = google_results)


def generate_wot(query, filepath):
  """
    Takes a query and path to a parsed version of a file
    and returns a window of text around non-stopword
    keywords of 'query'

    Params:
      query - Query that the user passed in.  Stopword
        removal will be performed on this query before 
        looking for a suitable window of text
      filepath - filepath to the parsed version of the document

    Returns:
      A string containing a suitable window of text. May be ""
        if no suitable line was found
  """

  window = ""
  #modified query with stopwords removed
  mod_query = metapy.index.Document()
  mod_query.content(query)
  #Remove the <s> boundary tags MeTA generates
  tok = metapy.analyzers.ICUTokenizer(suppress_tags=True)
  tok = metapy.analyzers.ListFilter(tok, 
                                    "stopwords.txt", 
                                    metapy.analyzers.ListFilter.Type.Reject)
  tok.set_content(mod_query.content())

  #  We're going to search every line in the parsed document
  #   and count how many times a keyword matches a line 
  #  The line with the most keyword matches will be returned
  query_words = [token for token in tok]

  # line-indexed array containing how many times line i
  #   matched a keyword
  line_matches = []

  with open(filepath, 'r+') as f:
    lines = f.readlines()
    line_matches = [0] * len(lines)
    for line_num, line in enumerate(lines):
      for word in query_words:
        #If we found a keyword in this line,
        # mark that this line matched this keyword
        pattern = '\\b{0}\\b'.format(word)
        num_keyword_matches = len(re.findall(pattern, line, re.IGNORECASE))

        if num_keyword_matches > 0:
          line_matches[line_num] += num_keyword_matches

    #Find the best-matching line
    best_line_index = line_matches.index(max(line_matches))
    best_line_num_matches = line_matches[best_line_index]
    print("Line #{0} had {1} matches".format(best_line_index, best_line_num_matches))

    #No suitable line was found, return ""
    if best_line_num_matches == 0:
      window = "" 
    else:
      #A best line was found, return that line
      window = lines[best_line_index]

    print(window)


  return window


@app.route('/raw_docs/<path:doc_request>')
def show_doc(doc_request):
  #local_ip = get_lan_ip
  return send_from_directory(pss.get_raw_docs_dir(), doc_request);

if __name__ == '__main__':

  print("Creating PSS_Runner object")

  #Initialize the PSS_Runner
  pss = PSS.PSS_Runner(os.getcwd(), "config.toml")

  #Set parser mappings
  parser_mappings = {
    'header_files': PSS.copy_parser_function,
    'mp_docs':      PSS.stupid_parse_file2,
    'angrave_book': PSS.html_parser_function,
    'pdfs':         PSS.pdf_parser_function
  }

  pss.parser_mappings = parser_mappings

  #Set collection weights
  weights = {
    'header_files': 1,
    'angrave_book': 5,
    'pdfs'        : 1,
    'mp_docs'     : 3,
  }

  pss.weights = weights
  pss.parse_raw_docs()
  pss.generate_index()

  print("PSS_Runner Created Successfully")

  app.run(host='0.0.0.0')
