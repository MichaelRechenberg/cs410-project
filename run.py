from flask import Flask, render_template, request, url_for

app = Flask(__name__)

# loads the default query form
@app.route('/')
def form():
	return render_template('query.html')

# deals with showing the response
@app.route('/handler/', methods=['POST'])
def handler():
	query = request.form['queryPost']
	return render_template('response.html', query=query)

# run
if __name__ == '__main__':
	app.run()