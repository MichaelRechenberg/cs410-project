# CS 410
# generate the window of text around the query given a query and
# a filepath to a parsed document (.txt) that has
# the query in it

import os

def generate_wot(query, filepath):
	file_dir = os.path.dirname(os.path.abspath(__file__))
	full_filepath = os.path.join(file_dir, filepath)


	window = ""
	with open(full_filepath, 'r+') as f:
		for line in f:
			if query in line:

				window = line
				break


	return window