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
testdoc.text = defs.generate_wot("hello", "raw/hello.txt")

@app.route('/')
def form():
	return render_template('query.html')

# deals with showing the response
@app.route('/handler/', methods=['POST'])
def handler():
	query = request.form['queryPost']
	docs = [testdoc]
	return render_template('response.html', query=query, docs=docs)

# run
if __name__ == '__main__':
	app.run()
