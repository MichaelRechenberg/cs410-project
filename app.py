from flask import Flask, render_template, request, url_for, send_from_directory
import os
import socket

pss = None

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
	return render_template('query.html')

@app.route('/reponse', methods = ['POST'])
def response():
	query = request.form['query']
	#list parsed = scoreQuery
	return render_template('response.html', query = query)

@app.route('/raw/<path:doc_request>')
def show_doc(doc_request):
	#local_ip = get_lan_ip
	return send_from_directory('raw', doc_request);

if __name__ == '__main__':
	app.run(host='0.0.0.0')
