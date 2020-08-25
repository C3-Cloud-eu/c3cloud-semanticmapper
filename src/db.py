# -*- coding: utf-8 -*-
import sqlite3
import re
from time import time
from sqlite3 import IntegrityError
from os import remove
from os.path import isfile
import helpers as h
from helpers import csv_to_documents
from contextlib import contextmanager
import logging
## import pandas as pd

from objects import *

log = logging.getLogger('mapper')

db_file = 'db/sqlitedb'

text = "TEXT"
integer = "INTEGER"

# table names
DB_sites = 'sites'
DB_code_systems = 'code_systems'
DB_concepts = 'concepts'
DB_equivalences = 'equivalences'
DB_codes = 'codes'
# DB_sites_code_systems = 'sites_code_systems'
DB_mappings = 'mappings'

# all_tables = [DB_sites, DB_code_systems, DB_concepts,
#              DB_equivalences, DB_codes, DB_sites_code_systems, DB_mappings]

all_tables = [DB_sites, DB_code_systems, DB_concepts,
              DB_equivalences, DB_codes, DB_mappings]

@contextmanager
def wcursor(readonly=False):
    global db
    if readonly:
        db = sqlite3.connect(f'file:{db_file}?mode=ro', uri=True)
    else:
        db = sqlite3.connect(db_file)
    ## db.row_factory = sqlite3.Row
    c = db.cursor()

    try:
        yield c
    except Exception as e:
        print(e)
        db.rollback()
        raise e
    else:
        if not readonly:
            # db.commit()
            commit_and_rebuild()
    c.close()
    
def execute(cursor, r, a, verbose=False):
    if verbose:
        log_execute(r, a)
    cursor.execute(r, a)

def commit_and_rebuild():
    db.commit()
    rebuild_all()

def mkjoin(a,b,fk,pk):
    return f"{a} inner join {b} on ({a}.{fk} = {b}.{pk})"

# def sqlitedf(e):
#     return pd.DataFrame.from_records(data=e, columns=e[0].keys())

def rebuild_all():
    global concepts
    global code_systems
    build_all_mappings()
    build_all_sites()
    build_all_codes()
    build_all_equivalences()
    concepts = list_all_concepts()
    code_systems = build_all_code_systems()

    
def build_all_code_systems():
    with wcursor(readonly=True) as cursor:
        values = cursor.execute("select uri, code_system, version from code_systems").fetchall()
    return [h.dictFromKeyValues([h.CODE_SYSTEM_URI, h.CODE_SYSTEM, h.CODE_SYSTEM_VERSION], v) for v in values]


def build_all_equivalences():
    global equivalences
    keys = list_column('equivalences', 'equivalence')
    values = list_column('equivalences', 'definition')
    equivalences = h.dictFromKeyValues(keys, values)
    # log.warning('EQUIVALENCES: {}'.format(equivalences))

def build_all_sites():
    global sites
    sites = list_column('sites', 'site')


def build_all_codes():
    global codes
    with wcursor(True) as cursor:
        cursor.execute('SELECT code, code_systems.code_system, designation, uri from {}'
                       .format(mkjoin('codes','code_systems','code_system','oid')))
        ans = cursor.fetchall()
        codes = [h.dictFromKeyValues([h.CODE, h.CODE_SYSTEM, h.DESIGNATION, h.CODE_SYSTEM_URI], e)
                    for e in ans]
        ## print(codes)



# TODO use a temporary table ?
def build_all_mappings():
    global mappings
    query = '''
select concepts.concept,cs.code_system,cs.uri,c.code,c.designation,s.site
 from mappings m
 inner join codes c on (m.code = c.oid)
 inner join concepts on (m.concept = concepts.oid)
 inner join sites s on (m.site = s.oid)
 inner join code_systems cs on (c.code_system = cs.oid);
'''    
    columns = [h.CONCEPT, h.CODE_SYSTEM, h.CODE_SYSTEM_URI, h.CODE,
               h.DESIGNATION, h.SITE]
    with wcursor(True) as cursor:
        mappings = [h.dictFromKeyValues(columns, e)
                    for e in cursor.execute(query).fetchall()]
    ## log.warning(f'mappings: {mappings[:2]}')

    

# get the fk corresponding to a certain row in a table
def fetch_fk(table, column, value):
    log.warning("fetch_fk {} {} {}".format(str(table), str(column), str(value)))
    # this is for security against injections.
    # it's bad and dirty. but why not. TODO peewee ?
    assert table in all_tables
    assert re.match('^[a-zA-Z_]+$', column)
    
    s = 'SELECT oid FROM {} WHERE {}=?'.format(table, column)
    with wcursor(True) as cursor:
        fks = cursor.execute(s, (value,)).fetchall()
        
    log.warning(str(fks))
    assert len(fks) == 1, "error with [{}] -> [{}]".format(s, fks)
    return fks[0][0]

    
def list_column(table, column):
    with wcursor(True) as cursor:
        cursor.execute('SELECT {} from {}'.format(column, table))
        ans = [e[0] for e in cursor.fetchall()]
    return ans
    
    
def count_rows(table, where):
    query = 'select count(*) from {} where {}'.format(table, where)
    with wcursor(True) as cursor:
        ans = cursor.execute(query).fetchone()
    return ans
    
    # TODO function 'firstcolumn' to get the first elements of a fetchall
    
    
def list_all_concepts(concept=''):  # todo: remove the argument
    with wcursor(True) as cursor:
        ans = [e[0] for e in cursor.execute(
            'select concept from concepts',
            ).fetchall()]
    return ans if concept=='' else [e for e in ans if e == concept]
    
    
def list_all_sites():
    with wcursor(True) as cursor:
        ans = [e[0] for e in cursor.execute(
            'select site from sites'
            ).fetchall()]
    return ans
    
    
def list_all_mappings(site="", concept=""):
    log.warning(str([concept, site]))
    return [m for m in mappings
            if (concept == "" or m[h.CONCEPT] == concept)
            and (site == "" or m[h.SITE] == site)]


def list_all_codes(site=''):

    ans = query_perhaps_condition(
        condition='where s.site=?',
        query='''
select c.code, cs.code_system, cs.uri, c.designation
 from mappings m
 inner join codes c on (m.code=c.oid)
 inner join code_systems cs on (c.code_system=cs.oid)
 inner join sites s on (m.site=s.oid)
 {}
''')(site)
    return [h.dictFromKeyValues(
        [h.CODE, h.CODE_SYSTEM, h.CODE_SYSTEM_URI, h.DESIGNATION],
        e) for e in ans]


def list_all_code_systems():
    keys = [h.CODE_SYSTEM_URI, h.CODE_SYSTEM, h.CODE_SYSTEM_VERSION]
    with wcursor(True) as cursor:
        values = cursor.execute("select uri, code_system, version from code_systems").fetchall()
    return [h.dictFromKeyValues(keys, v) for v in values]
    
    
def list_concepts():
    query = 'select oid,concept from concepts'
    with wcursor(True) as cursor:
        ans = cursor.execute(query).fetchall()
    return ans
        
    
def code_details_with_site(code, code_system_uri, site):
    # from code details fetching
    # fromCode_details = db.code_details(code, code_system)
    req_fromcode_oid = '''
select c.oid,cs.code_system,cs.uri,cs.version,c.code,c.designation
 from mappings m
 inner join codes c on (c.oid=m.code)
 inner join code_systems cs on (c.code_system=cs.oid)
 inner join sites s on (s.oid=m.site)
 where c.code_system=(select oid from code_systems
                      where uri=:uri)
       and s.site=:site
       and c.code=:code
'''

    with wcursor(True) as cursor:
        fromcodedetails = cursor.execute(
            req_fromcode_oid,
            {'uri': code_system_uri, 'code': code, 'site': site}).fetchall()
    
    if not len(fromcodedetails):
        return "no such code: {}@{}".format(code, code_system_uri), 404

    keys = ["id", h.CODE_SYSTEM, h.CODE_SYSTEM_URI,
            h.CODE_SYSTEM_VERSION, h.CODE, h.DESIGNATION]
    code_details = h.dictFromKeyValues(keys, fromcodedetails[0])
    code_details['site'] = site
    return code_details
    
    
def conceptForCode(code='', code_system='', site=''):
    log.warning("searching for {} -- {} -- {}".format(code, code_system, site))
    c = list(set([e[h.CONCEPT]
            for e in mappings
            if e[h.CODE] == code
            and e[h.CODE_SYSTEM_URI] == code_system
            and (site == ''
                 or e[h.SITE] == site)]))
    log.warning(c)
    return c


def query_perhaps_condition(query, condition):
        ## log.warning("$$$$$$$$$ {}".format(query.format(condition)))
        
        def ans(arg):
            if(arg == ""):
                def f():
                    with wcursor(True) as cursor:
                        return cursor.execute(query.format('')).fetchall()
            else:
                def f():
                    with wcursor(True) as cursor:
                        return cursor.execute(query.format(condition), (arg,)).fetchall()
            return f()  # [e[0] for e in f().fetchall()]
        return ans


    
# :    : string -> [string] -> [a] -> oid
def insertMaybe(dbname, cols, vals):    
    log.warning(f"---- insert maybe ---- {dbname} {cols} {vals}")
    if not isinstance(vals, dict) and not isinstance(vals, tuple):
        vals = (vals,)
    log.warning("insertmaybe {} {} {}".format(dbname, cols, vals))
    if isinstance(vals, dict):
        qmarks = '(' + ','.join([':'+k for k in vals.keys()]) + ')'
    else:
        qmarks = '(' + (','.join(['?']*len(vals))) + ')'
    log.warning("qmarks: {}".format(qmarks))
    with wcursor(False) as cursor:
        try:
            colsstr = '(' + ','.join(cols) + ')'
            s = 'INSERT INTO {} {} VALUES {}'.format(dbname,
                                                     colsstr,
                                                     qmarks)
            cursor.execute(s, vals)
            log.warning(f"insertion successful: {dbname} {cols} {vals}")
            return cursor.lastrowid
        except IntegrityError as e:
            log.warning('####@@@@  catched IntegrityError  @@@@####')
            log.warning('{} already in db'.format(vals))
    
    
def log_execute(req, args=''):
    log.warning("############################")
    log.warning(req)
    log.warning(args)
    log.warning("############################")


def delete_mapping(site=None, concept=None):
    log.warning('XXXXXXXX deleting mapping {}@{}'.format(concept, site))
    assert (site is not None) or (concept is not None)
    
    d = { 'site': site, 'concept': concept }
    where = ' and '.join(  [f"{k}=(select oid from {k}s where {k}=:{k})" for k, v in d.items() if v is not None] )
    request = f"delete from mappings where {where}"

    with wcursor(False) as cursor:
        try:
            d = h.dictFromKeyValues(
                [h.SITE, h.CONCEPT],
                [site, concept])
            log_execute(request, d)
            cursor.execute(request, d)
            ans = {'modified_mappings': cursor.rowcount}
            log.warning(ans)
            
            # delete_code_for_concept(cursor, site=site, concept=concept)
            req = f'''
        delete from codes
          where oid in (select m.code from mappings m where {where})
        '''
            cursor.execute(req, {'site': site, 'concept': concept})
        except Exception as e:
            log.error("!!!! error deleting the mapping")
            log.error(e)
            log.error(request)
            log.error(d)
            db.rollback()
            raise e
    commit_and_rebuild()
    return ans


def set_code(c):
    set_code_system(c.code_system)
    already = [cc for cc in codes if cc[h.CODE] == c.code
               and cc[h.DESIGNATION] == c.designation
               and cc[h.CODE_SYSTEM_URI] == c.code_system.uri]
    if len(already):
        log.warning("{} already in db: {}".format(c, already))
    else:
        with wcursor(False) as cursor:
            request = '''
insert into codes (code, code_system, designation)
 values (?,
        (select oid from code_systems where uri=?),
  ?)
'''
            cursor.execute(
                request,
                (c.code, c.code_system.uri, c.designation))
            log.warning("{} rows modified in codes".format(cursor.rowcount))    


def set_mapping(m):
    assert(type(m) == Mapping)
    assert(all([type(e) == Code for e in m.codes]))
    log.warning('setting mapping for <{}>@<{}>: {}'.format(m.concept, m.site, m.codes))
    
    delete_mapping(site=m.site, concept=m.concept)
    set_site(m.site)
    set_concept(m.concept)
    for c in m.codes:
        set_code(c)
        
    
    request = '''
insert into mappings (site, concept, code, equivalence)
 values ((select oid from sites where site=:site),
         (select oid from concepts where concept=:concept),
         (select oid from codes where code=:code
             and code_system=(select oid from code_systems where uri=:code_system_uri)
             and designation=:designation),
         (select oid from equivalences where equivalence=:equivalence))
'''
    rowcount = 0

    with wcursor() as cursor:
        try:
            for c in m.codes:
                args = {h.SITE: m.site,
                        h.CONCEPT: m.concept,
                        h.CODE: c.code,
                        h.CODE_SYSTEM_URI: c.code_system.uri,
                        h.DESIGNATION: c.designation,
                        h.EQUIVALENCE: m.equivalence}
                execute(cursor, request, args, verbose=True)
            rowcount = cursor.rowcount
            log.warning("{} rows modified in codes".format(rowcount))
        except Exception as e:
            log.warning(e)
            log.warning(f"ERROR (cf above): this mapping is already there {m} <<{c}>>")
            db.rollback()
            raise e
    build_all_mappings()
    return {'modified_mappings': rowcount}

    


def delete_code_system(code_system):
    log.warning("delete code system <{}>".format(code_system))
    assert code_system is not None, "error, must specify site and concept to delete codes"
    req = '''
delete from code_systems
  where code_system=?
'''
    with wcursor(False) as cursor:
        cursor.execute(req, (code_system,))
        return cursor.rowcount


def set_code_system(cs):
    log.warning("set code system {}".format(cs))
    assert type(cs) == CodeSystem
    
    rc = 0
    row = [ e for e in code_systems if e[h.CODE_SYSTEM] == cs.code_system ]
    if len(row) == 0:
        log.warning("new code system")
        rowid = insertMaybe(
            dbname=DB_code_systems,
            cols=['code_system', 'uri', 'version'],
            vals=(cs.get_code_system(), cs.get_uri(), 'unknown'))
        rc=1
    else:
        row = [e for e in row if e[h.CODE_SYSTEM_URI] == cs.uri ]
        if len(row):
            log.warning(f"cs already there {row} {cs}")
        else:
            log.warning(f"Updating existing code system {row} {cs}")
            req = '''UPDATE code_systems 
 set uri=:urival,version=:verval
 where code_system=:csval
'''
            with wcursor(False) as cursor:
                cursor.execute(req, {'urival': cs.uri,
                                    'verval': 'unknown',
                                    'csval':  cs.code_system})
                rc = cursor.rowcount
    return {'modified_code_systems': rc}


def set_concept(concept):
    with wcursor(True) as cursor:
        c = cursor.execute('select * from concepts where concept=:concept',
                           {'concept': concept}).fetchall()
    if(len(c)):
        return {'already exist': c[0]}
    else:
        log.warning(f"new concept ({concept})")
        
    insertMaybe(
        dbname=DB_concepts,
        cols=['concept'],
        vals=concept)
    return {'modified_concepts': cursor.rowcount}


def delete_concept(concept):
    assert(len(concept))
    request = '''
delete from concepts
where concept=:concept
'''
    with wcursor(False) as cursor:
        cursor.execute(request, {'concept': concept})
        ans = {'modified_concepts': cursor.rowcount}
    ans.update( delete_mapping(concept = concept) )
    log.warning(ans)
    return ans

def set_site(site):
    if site not in sites:
        insertMaybe(
            dbname=DB_sites,
            cols=['site'],
            vals=site)
        return 1
    else:
        return 0

def connect_database():
    global db
    db = sqlite3.connect(db_file)
    return db


def create_database():
    connect_database()
    with wcursor(False) as cursor:
        def create_table(name, columns):
            s = ('CREATE TABLE {}({});'.format(name, columns))
            log.warning(s)
            cursor.execute(s)
    
        if isfile(db_file):
            open(db_file, 'w').close()
            # remove(db_file)
        connect_database()
    
        def column(name, datatype=text, fk=None, primary=False, unique=False):
            e = {'primary': primary, 'unique': unique}
            if fk is not None:
                e['fk'] = fk
                datatype = integer
            e['datatype'] = datatype
            return name, e
    
        # def fk(name, args):
        #     return column(name, fk=name + 's', *args)
    
        def table(name, *l):
            return name, {k: e for k, e in l}
    
        tables = [
            table(DB_sites, column('site', unique=True)),
            table(
                DB_code_systems,
                column('code_system', unique=True),
                column('uri'),
                column('version')),
            table(DB_concepts, column('concept', unique=True)),
            table(
                DB_equivalences,
                column('equivalence', unique=True),
                column('definition')),
            table(
                DB_codes,
                column('code', unique=True),
                column('code_system', fk=DB_code_systems, unique=True),
                column('designation', unique=True)),
            # table(
            #     DB_sites_code_systems,
            #     column('site', fk=DB_sites, unique=True),
            #     column('code_system', fk=DB_code_systems, unique=True)),
            table(
                DB_mappings,
                column('concept', fk=DB_concepts, unique=True),
                column('code', fk=DB_codes, unique=True),
                column('site', fk=DB_sites, unique=True),
                column('equivalence', fk=DB_equivalences))
        ]
    
        for name, fields in tables:
    
            def str_uniques():
                luniq = [k for k, v in fields.items() if v['unique']]
                return '' if len(luniq) == 0 else ", unique ({})".format(
                    ','.join(luniq))
    
            s = ",".join([
                k
                + " " + v['datatype']
                + ('' if not v['primary'] else 'PRIMARY KEY')
                + ('' if 'fk' not in v else ' REFERENCES {}(oid)'.format(v['fk']))
                for k, v in fields.items()]) + str_uniques()
    
            log.warning(f'{name} -- {s}')
            create_table(name, s)
            
        connect_database()
    
        # populate the equivalences
        # relatedto | equivalent | equal | wider | subsumes
        # | narrower | specializes | inexact | unmatched | disjoint
        conceptMapEquivalences = csv_to_documents("data/conceptMapEquivalences.csv")
        log.warning(conceptMapEquivalences)
        for e in conceptMapEquivalences.values():
            insertMaybe(
                dbname=DB_equivalences,
                cols=['equivalence', 'definition'],
                vals=e)
        db.commit()
    rebuild_all()
    ## ## done from client side
    # populate_db()


def init():
    commit_and_rebuild()
