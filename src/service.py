from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from webargs import fields
from webargs.flaskparser import use_args
import json
import helpers as h
import db
import mapper
import logging
from objects import *

########### DEMO ############

import os
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader

from functools import wraps

log = logging.getLogger('service')

env = Environment(
##    loader=PackageLoader(package_name='app', package_path='templates'),
    loader=FileSystemLoader('templates/'),
    autoescape=select_autoescape(['html', 'xml']),
    extensions=['pypugjs.ext.jinja.PyPugJSExtension'],
    variable_start_string="[[",  # avoid conflicts with Vue.js
    variable_end_string="]]"
)

template = env.get_template('template.pug')

BASE_URL = "/c3-cloud"
app = Flask(__name__, static_url_path=BASE_URL)
app.url_map.strict_slashes = False
CORS(app)

###########
# Routing #
###########

maybeStr = fields.Str(missing=u"")


def mkresp(l):
    return jsonify({"count": len(l), "data": l})


def getter(f, args):
    return mkresp(f() if args is None
                  else f(*args) if isinstance(args, tuple) else f(**args))


# db.list_all_mappings , mapper.set_mapping
def request_handler(fget, fpost, fdelete):
    def f(method, args):
        if method == 'GET':
            return getter(fget, args)
        elif method == 'POST':
            ans, code = fpost(args)
            return jsonify(ans), code
        elif method == 'DELETE':
            ans, code = fdelete(args)
            return jsonify(ans), code
    return f

######

with open("./apikey", 'r') as f:
    APIKEY = f.read()

# decorator for requiring the api key for modifying data
def require_appkey(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        k = request.headers.get('key')
        if request.method=="GET" or (k and k == APIKEY):
            return view_function(*args, **kwargs)
        else:
            log.warning("access to {} denied.".format(request.url))
            log.warning(str(request.headers))
            abort(401)
    return decorated_function

######

@app.route(BASE_URL + '/')
def home():
    # return "ok!"
    return template.render()


@app.route(BASE_URL + '/demo')
def demo():
    # return send_from_directory('templates', 'template.html')
    return template.render()


@app.route(BASE_URL + '/translate', methods=['GET'])
@use_args({'fromSite':    maybeStr,
           'code':        maybeStr,
           'code_system': maybeStr,
           'toSite':      maybeStr})
def translate(args):
    log.warning('======== translate ========')
    ans, code = mapper.translate(**{k: request.args.get(k) for k in args})
    if code == 200:
        return jsonify(ans)
    else:
        return ans, code, {'Content-Type': 'text/plain'}


@app.route(BASE_URL + '/mappings/', methods=['GET', 'POST'])
@use_args({
    'site': maybeStr,
    'concept': maybeStr
    })
@require_appkey
def mapping(args):
    log.warning('======== mappings ========')
    
    if request.method == 'GET':
        return getter(db.list_all_mappings, args)
    else:
        bodyjson = request.get_json()
        # if type(bodyjson) == str:
        #     bodyjson = json.loads(bodyjson)
        # print(bodyjson)
        if "old" in bodyjson.keys():
            m_old = Mapping(**bodyjson['old'])
            if not "new" in bodyjson.keys():
                return "must specify the new mapping along with the old one", 400
            
            m = Mapping(**bodyjson['new'])
        else:
            m_old = None
            m = Mapping(**bodyjson)
        ans, code = mapper.set_mapping(m, m_old)
        return jsonify(ans), code

    log.warning(args['codes'])
    return request_handler(
        db.list_all_mappings,
        mapper.set_mapping)(request.method, args)


@app.route(BASE_URL + '/code-systems', methods=['GET', 'POST'])
@use_args({'uri': fields.Str(),
           h.CODE_SYSTEM: fields.Str(),
           h.CODE_SYSTEM_VERSION: maybeStr,
           })
@require_appkey
def code_systems(args):
    if request.method == 'GET':
        return getter(db.list_all_code_systems, None)
    else:
        log.warning('================================', args)
        cs = CodeSystem(**{k: v for k, v in args.items() if k in ['uri','code_system']})
        ans, code = mapper.set_code_system(cs)
        return jsonify(ans), code

@app.route(BASE_URL + '/codes', methods=['GET', 'POST'])
@use_args({'site': maybeStr})
@require_appkey
def codes(args):
    log.warning("#codes#")
    if request.method == 'GET':
        return getter(db.list_all_codes, args)
    else:
        return None

@app.route(BASE_URL + '/concepts', methods=['GET', 'POST', 'DELETE'])
@use_args({'concept': maybeStr})
@require_appkey
def concepts(args):
    return request_handler(
        fget=db.list_all_concepts,
        fpost=mapper.set_concept,
        fdelete=mapper.delete_concept)(request.method, args)



@app.route(BASE_URL + '/sites', methods=['GET', 'POST'])
@require_appkey
def sites():
    return request_handler(
        db.list_all_sites,
        mapper.set_site)(request.method, None)


@app.route(BASE_URL + '/all', methods=['GET', 'DELETE'])
@require_appkey
def getall():
    ## TODO: is this really needed?
    if request.method == 'DELETE':
        db.create_database()
        log.warning('/!\\ DELETE DB /!\\')
        return 'fresh start: database is empty'
    else:
        return mkresp({
            'sites': db.list_all_sites(),
            'mappings': db.list_all_mappings(),
            'concepts': db.list_all_concepts(),
            'code_systems': db.list_all_code_systems()
            })


# list(mapper.mappings)
# "sites":    db.list_column(db.DB_sites, 'site'),
# "codes":     list(mapper.codes),
# })

# print("set mapping")
# print(request.get_json())
# mapper.set_mapping(request.get_json())
# return "yolo"
