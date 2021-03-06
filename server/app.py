from __future__ import print_function

import os
import time

import six
import argparse
import sys
from flask import Flask, url_for, jsonify, render_template, request, abort, flash
import json
from pymongo import MongoClient
from werkzeug.utils import secure_filename

from components.standalone_parser import StandaloneParser

app = Flask(__name__)
client = MongoClient()
UPLOAD_FOLDER = '/usr1/home/fangzhex/tranx_user_study_uploads'
ALLOWED_EXTENSIONS = {'zip'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PARSERS'] = dict()


def init_arg_parser():
    arg_parser = argparse.ArgumentParser()

    #### General configuration ####
    arg_parser.add_argument('--cuda', action='store_true', default=False, help='Use gpu')
    arg_parser.add_argument('--config_file', type=str, required=True,
                            help='Config file that specifies model to load, see online doc for an example')
    arg_parser.add_argument('--port', type=int, required=False, default=8081)

    return arg_parser


@app.route("/")
def default():
    return render_template('default.html')


@app.route("/visualize")
def visualize():
    return render_template('visualize.html')


@app.route('/parse/<dataset>', methods=['GET'])
def parse(dataset):
    utterance = request.args['q']

    parser = app.config['PARSERS'][dataset]

    if six.PY2:
        utterance = utterance.encode('utf-8', 'ignore')

    hypotheses = parser.parse(utterance, debug=True)

    responses = dict()
    responses['hypotheses'] = []

    for hyp_id, hyp in enumerate(hypotheses):
        # print('------------------ Hypothesis %d ------------------' % hyp_id)
        # print(hyp.code)
        # print(hyp.tree.to_string())
        # print(hyp.score.item())
        # print(hyp.rerank_score.item())

        # print('Actions:')
        # for action_t in hyp.action_infos:
        #     print(action_t)

        actions_repr = [action.__repr__(True) for action in hyp.action_infos]

        hyp_entry = dict(id=hyp_id + 1,
                         value=hyp.code,
                         tree_repr=hyp.tree.to_string(),
                         score=hyp.rerank_score.item() if hasattr(hyp, 'rerank_score') else hyp.score.item(),
                         actions=actions_repr)

        responses['hypotheses'].append(hyp_entry)

    return jsonify(responses)


@app.route("/upload", methods=['POST'])
def upload():
    try:
        req_data = request.get_json()
        db = client['tranx']
        collection = db['events']
        req_data['timestamp'] = int(time.time())
        collection.insert_one(req_data)
        return "success"
    except Exception as e:
        print(e)
        return "failed"


@app.route("/browser_log", methods=['POST'])
def browser_log():
    try:
        req_data = request.get_json()
        db = client['tranx']
        collection = db['browser_events']
        req_data['server_timestamp'] = int(time.time())
        collection.insert_one(req_data)
        return "success"
    except Exception as e:
        print(e)
        return "failed"


@app.route("/keylog", methods=['POST'])
def keylog():
    try:
        req_data = request.get_json()
        db = client['tranx']
        collection = db['keylog_events']
        req_data['server_timestamp'] = int(time.time())
        collection.insert_one(req_data)
        return "success"
    except Exception as e:
        print(e)
        return "failed"


@app.route("/post_task_study", methods=['POST'])
def post_task_study():
    try:
        req_data = request.get_json()
        db = client['tranx']
        collection = db['post_task_survey']
        req_data['server_timestamp'] = int(time.time())
        collection.insert_one(req_data)
        return "success"
    except Exception as e:
        print(e)
        return "failed"


@app.route("/user_timeline_log", methods=['POST'])
def user_timeline_log():
    try:
        req_data = request.get_json()
        db = client['tranx']
        collection = db['user_timeline']
        req_data['server_timestamp'] = int(time.time())
        collection.insert_one(req_data)
        return "success"
    except Exception as e:
        print(e)
        return "failed"


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def authorized(filename):
    splits = filename.rsplit('_', 2)
    if len(splits) == 3:
        userid = splits[0]
        task = splits[1]
        db = client['tranx']
        collection = db['user_assignments']

        for record in collection.find({'userid': userid,
                                       'completion_status': 0}):
            if task == record['task']:
                set_as_complete(collection, record['_id'])
                return True
    return False


def set_as_complete(collection, obj_id):
    collection.update_one({'_id': obj_id}, {'$set': {'completion_status': 1}})


@app.route("/task_submission", methods=['POST'])
def submit():
    # check if the post request has the file part
    if 'file' not in request.files:
        return '', 401
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return '', 401
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        if authorized(filename):
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return '', 200
    return '', 401


@app.route("/assign_task", methods=['POST'])
def assign_task():
    req_data = request.get_json()
    userid = req_data['userid']
    db = client['tranx']
    collection = db['user_assignments']
    results = []
    for record in collection.find({'userid': userid,
                                   'completion_status': 0}):
        results.append({'task': record['task'], 'use_plugin': record['use_plugin']})
    return jsonify(results)


@app.route("/get_all_userids", methods=['GET'])
def get_all_userids():
    db = client['tranx']
    collection = db['user_assignments']
    results = []
    for record in collection.distinct('userid'):
        results.append(record)
    return jsonify(results)


@app.route("/get_all_completed_userids", methods=['GET'])
def get_all_completed_userids():
    db = client['tranx']
    collection = db['user_assignments']
    results = []
    for userid in collection.distinct('userid'):
        if not collection.count({'userid': userid,
                                 'completion_status': 0}):
            results.append(userid)
    return jsonify(results)


@app.route("/get_user_status", methods=['POST'])
def user_task_status():
    req_data = request.get_json()
    userid = req_data['userid']
    db = client['tranx']
    collection = db['user_assignments']
    results = []
    for record in collection.find({'userid': userid}):
        results.append({'task': record['task'],
                        'use_plugin': record['use_plugin'],
                        'completion_status': record['completion_status']})
    return jsonify(results)


if __name__ == '__main__':
    args = init_arg_parser().parse_args()
    config_dict = json.load(open(args.config_file))

    for parser_id, config in config_dict.items():
        parser = StandaloneParser(parser_name=config['parser'],
                                  model_path=config['model_path'],
                                  example_processor_name=config['example_processor'],
                                  beam_size=config['beam_size'],
                                  reranker_path=config['reranker_path'],
                                  cuda=args.cuda)

        app.config['PARSERS'][parser_id] = parser

    app.run(host='0.0.0.0', port=args.port, debug=True)
