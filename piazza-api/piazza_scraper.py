#Run this script to and follow prompts to scrape your piazza page
#Simply git clone https://github.com/hfaran/piazza-api.git
# and then run this script in the piazza-api directory

import json
from piazza_api import Piazza
import pprint
p = Piazza()

class_id = ''
class_id = input('Enter id of the class you want to scrape\n')
#A prompt will show up and you'll add your info
p.user_login()

class_to_scrape = p.network(class_id)
posts = class_to_scrape.iter_all_posts(limit=1)

with open('dump_' + class_id,  'w+') as json_file:
  for post in posts:
    pprint.pprint(post)
    # main content of the post
    #main_post_text = post['history'][0]['content'])
    children = post['children']
    print(children)





