from flask import Flask, render_template, request, url_for
import defs

app = Flask(__name__)

# loads the default query form

class Document():
	file = ""
	link = ""
	text =""

testdoc = Document()
testdoc.file = defs.make_filename("raw/hello.txt")
testdoc.link = "https://testsite.com/hello.txt"
testdoc.text = defs.generate_wot("test", "raw/hello.txt")

seconddoc = Document()
seconddoc.file = defs.make_filename("raw/test.txt")
seconddoc.link = "https://testsite.com/test.txt"
seconddoc.text = defs.generate_wot("test", "raw/test.txt")

@app.route('/')
def form():
	return render_template('query.html')

# deals with showing the response
@app.route('/handler/', methods=['POST'])
def handler():
	query = request.form['query']
	docs = [testdoc, seconddoc]
	return render_template('response.html', query=query, docs=docs)

# run
if __name__ == '__main__':
	app.run()
