import html
import time
import os
from flask import Flask, flash, request, redirect, url_for, render_template, Response
from werkzeug.utils import secure_filename
from flask import send_from_directory , Markup, send_file
import subprocess
import pickle
import ntpath
import Phanns_f
import ann_config
from keras.models import load_model
import tensorflow as tf
from flask_socketio import SocketIO, emit
from random import *
import json


ROOT_FOLDER = os.path.dirname(os.path.realpath(__file__)) 
UPLOAD_FOLDER = ROOT_FOLDER + '/uploads'
ALLOWED_EXTENSIONS = set(['txt', 'faa', 'fasta', 'gif', 'fa'])
import urllib
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"   # see issue #152
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["KERAS_BACKEND"]="tensorflow"
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['FASTA_SIZE_LIMIT']=500

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#app.config['APPLICATION_ROOT']='/adrian_net'
app.config['APPLICATION_ROOT']='/phanns'
#app.config['APPLICATION_ROOT']=''
PREFIX=app.config['APPLICATION_ROOT'] 
graph = tf.get_default_graph()

#socketio = SocketIO(app,async_mode='threading',ping_timeout=60000)
socketio = SocketIO(app,ping_timeout=60000)
def fix_url_for(path, **kwargs):
    return PREFIX + url_for(path, **kwargs)

@app.context_processor
def contex():
    return dict(fix_url_for = fix_url_for)

#add the sorable attribute to tables generated by pandas
@app.template_filter('sorttable')
def sorttable_filter(s):
    s= s.replace('table id=','table class="sortable" id=')
    return s


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/error/<error_msg>')
def error(error_msg):
    error_text=error_msg
    #if (error_msg == '1'):
    #    error_text="Too many sequences, got " + str(test.g_total_fasta) + " but limit is " + str(app.config['FASTA_SIZE_LIMIT'])
    return render_template('error.html',error_msg=error_text)

@app.route('/uploads/<filename>')
def bar(filename):
    print(filename)
    #return render_template('loading_t.html',filename=filename)
    test=Phanns_f.ann_result('uploads/'+filename)
    #(names,pp)=test.predict_score()
    (names,pp)=test.predict_score_test()
    return redirect(url_for('show_file',filename=filename))


@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('received my event: ' + str(json))
    test=Phanns_f.ann_result('uploads/'+json['filename'],request.sid,socketio)
    if ( test.g_total_fasta > app.config['FASTA_SIZE_LIMIT']):
        print ("fasta size : " + str(test.g_all_fasta))
        with app.app_context(), app.test_request_context():
            redict=url_for('error',error_msg="Too many sequences, got " + str(test.g_total_fasta) + " but limit is " + str(app.config['FASTA_SIZE_LIMIT']))
        socketio.emit('url', {'url':redict},room=request.sid)
    else:
        (names,pp)=test.predict_score_test()
        #(names,pp)=test.predict_score()
        redict=''
        with app.app_context(), app.test_request_context():
            redict=url_for('show_file',filename=json['filename'])
        socketio.emit('url', {'url':redict},room=request.sid)
    return True    

#@app.route('/', methods=['GET', 'POST'])
#def show_home():
#    return render_template('home.html')


#@app.route('/upload', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
         #   return redirect()
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            #print( fix_url_for('bar',filename=filename))
            #print( url_for('bar',filename=filename))
            return redirect(url_for('bar',filename=filename))
#    print( fix_url_for('upload_file'))
    return render_template('main.html')

@app.route('/about')
def about():
    return render_template('about.html', title='about')

@app.route('/saves/<filename>')
def show_file(filename):
    table_code_raw=pickle.load(open('saves/' + filename,"rb"))
    return render_template('index.html', table_code= table_code_raw, csv_table=os.path.splitext(ntpath.basename(filename))[0] + '.csv', filename_base=ntpath.basename(filename))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/downloads')
def downloads():
    return render_template('downloads.html')

@app.route('/download/<filename>')
def down_file(filename):
    if (filename == "model.tar"):
        return send_file('deca_model/model.tar')
    elif (filename == 'test.fasta'):
        return send_file('deca_model/test.fasta')
    elif (filename == 'PhANNs_DB.fasta.tgz'):
        return send_file('deca_model/PhANNs_DB.fasta.tgz')

@app.route('/csv_saves/<filename>')
def return_csv(filename):
	try:
		return send_file('csv_saves/' + filename)
	except Exception as e:
		return str(e)

if __name__ == "__main__":
    #app.run(debug=True, host="0.0.0.0", port=8080)
    #app.run(host="0.0.0.0", port=8080)
    #socketio.run(app,host="0.0.0.0", port=8080,ssl_context='adhoc')
    socketio.run(app,host="0.0.0.0", port=8080)
    #socketio.run(app, debug=True)
