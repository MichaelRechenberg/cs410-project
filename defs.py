# CS 410

import os

"""
generate the window of text around the query given a query and
a filepath to a parsed document (.txt) that has
the query in it
"""
def generate_wot(query, filepath):

	# get the directory of the file
	file_dir = os.path.dirname(os.path.abspath(__file__))
	full_filepath = os.path.join(file_dir, filepath)

	window = ""
	with open(full_filepath, 'r+') as f:
		for line in f:
			if query in line:

				splitLine = line.split(" ")
				if len(splitLine) > 20:
					#if there are more than 20 words, don't display
					#all of them
					window = cut_line(query, 20, line)
				else:
					window = line

				break


	return window

"""
cuts the line around the query to n words in front and behind it
"""
def cut_line(query, n, line):
	splitLines = line.split(query)

	if (len(splitLines) == 2):
		# the word appears only once

		before = splitLines[0]
		beforeWords = before.split(" ")
		after = splitLines[1]
		afterWords = after.split(" ")

		if len(beforeWords) > n/2:
			beforeWords = beforeWords[len(beforeWords) - n/2:]

		if len(afterWords) > n/2:
			afterWords = afterWords[:n/2]

		newLine = "..."
		for word in beforeWords[:-1]:
			newLine += word + " "
		newLine += beforeWords[-1]

		newLine += query

		for word in afterWords[:-1]:
			newLine += word + " "
		newLine += afterWords[-1]

		newLine += "..."
		return newLine

	else:
		# if there are multiple occurrences of query
		# a la google style... wip lol

		return line

"""
gets the filename from the filepath
"""
def make_filename(filepath):
	return os.path.splitext(filepath)[0]
