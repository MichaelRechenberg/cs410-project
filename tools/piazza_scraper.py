#
# Author: Michael Rechenberg
#
# Run this script to and follow prompts to scrape your piazza page
#   and generate a directory of documents that you can place in raw_docs

# Simply git clone https://github.com/hfaran/piazza-api.git
#   and then run this script in the piazza-api directory

import os
from piazza_api import Piazza
import pprint
from bs4 import BeautifulSoup


#Just a helper function, keep scrolling down...
def parse_children(obj, entry_list, level):
  """
    Recursively parses the dictionary that piazza-api retrieves and adds the
      followup discussion posts to entry_list

    Params:
      obj - Pass in top level object from piazza-api's iter_all_posts()
      entry_list - an empty list you want to append to
      level - level we are at in the discussion pass in 0 if you are calling this for the first time

    Returns:
      A list of tuples (html_text, level_of_entry)
  """


  #we've hit a leaf node
  if type(obj) is dict:

    #Add some metadata into our file
    if str(obj['type']) == 'i_answer':
      entry_list.append(("~Start Instructor Answer:", level))
    if str(obj['type']) == 's_answer':
      entry_list.append(("~End Student Answer:", level))
      
    if 'subject' in obj:
      entry_list.append((obj['subject'], level))
    if 'history' in obj:
      entry_list.append((child['history'][0]['subject'], level))
      entry_list.append((child['history'][0]['content'], level))

    if str(obj['type']) == 'i_answer':
      entry_list.append(("~End Instructor Answer:", level))
    if str(obj['type']) == 's_answer':
      entry_list.append(("~End Student Answer:", level))

    return entry_list

  #iterate through all the children in a DFS manner
  for child in obj:

    #Add some metadata into our file (not dealing with followup or feedback)
    if str(child['type']) == 'i_answer':
      entry_list.append(("~Start Instructor Answer:", level))
    if str(child['type']) == 's_answer':
      entry_list.append(("~Start Student Answer:", level))

    if 'subject' in child:
      entry_list.append((child['subject'], level))
    if 'history' in child:
      entry_list.append((child['history'][0]['subject'], level))
      entry_list.append((child['history'][0]['content'], level))

    if str(child['type']) == 'i_answer':
      entry_list.append(("~End Instructor Answer:", level))
    if str(child['type']) == 's_answer':
      entry_list.append(("~End Student Answer:", level))

    for child_num in range(len(child['children'])):
      entry_list = parse_children(child['children'][child_num], entry_list, level+1)


    
  return entry_list
   

#--------------------------------------------------------
#
#     The real meat and potatoes of this script
#
#--------------------------------------------------------

p = Piazza()

class_id = ''
print()
print('Enter the id of the class you want to scrape')
print('For example if the URL is https://piazza.com/class/ixno44ysm6i2u0')
print('You should enter ixno44ysm6i2u0')
print()
class_id = input('Id: ')

#A prompt will show up and you'll add your info
print('Enter your Piazza Login information')
p.user_login()

class_to_scrape = p.network(class_id)
posts = class_to_scrape.iter_all_posts(limit=None)

#Create the directory we will store the posts in
# named by dump_<class_id> 
dump_dir = 'dump_' + class_id
dump_dir = os.path.join(os.getcwd(), dump_dir)
try:
  os.mkdir(dump_dir)
except FileExistsError:
  pass


#Go through every post and create document for it, 
# named by the post's cid
for post_number, post in enumerate(posts):



  #cid of the post, unique identifier for each post
  cid = str(post['nr'])



  new_filename = os.path.join(dump_dir, cid)
  with open(new_filename, 'w+') as new_file:

    new_file.write("~Main Post:\n\n")

    new_file.write(post['history'][0]['subject'] + "\n")

    #Extract text of the main content of the post
    main_post_html = post['history'][0]['content']
    soup = BeautifulSoup(main_post_html, "html5lib")
    main_post_text = soup.get_text()
    new_file.write(main_post_text + "\n\n")

    #Gather the text of the followup discussions
    new_file.write("~Responses:\n\n")
    entry_list = []
    entry_list = parse_children(post['children'], entry_list, 0)
    for entry in entry_list:
      #Extract the text from the HTML string
      soup = BeautifulSoup(entry[0], "html5lib")
      entry_text = soup.get_text()
      #Indent the post for easier readability
      entry_text = "  "*entry[1] + entry_text
      new_file.write(entry_text + "\n")


    print("Finished scraping post {0} with cid {1}".format(post_number, cid))




