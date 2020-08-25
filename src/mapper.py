import logging
import os
import helpers as h
import schema
# import jsonschema
from functools import reduce
# from helpers import build_item
from objects import *
from fhir import FHIR
import db
from pathlib import Path

return_missing_params = 'missing parameters', 400

log = logging.getLogger('mapper')

def check_string(s):
    return s and len(s)


def check_parameters(*args):
    return all(map(check_string, args))


def translate(fromSite="", code="", code_system="", toSite=""):
    """
        this returns an HTTP code and a response body
    """
    log.warning("translate {}_{}@{} to {}".format(
        code_system, code, fromSite, toSite))
    # ommiting the destination site implies we want the reference code
    if fromSite != "CDSM" and len(toSite) == 0:
        toSite = "CDSM"

    # if not all(map(len, [fromSite, code, code_system, toSite])):
    #     return "Missing parameters", 400

    if not(check_parameters(fromSite, code, code_system, toSite)):
        return return_missing_params

    if not (fromSite in db.sites and toSite in db.sites):
        log.warning('error while searching for {} and {} in {}'.format(fromSite, toSite, db.sites))
        return "Unknown site", 400

    fromCode_details = db.code_details_with_site(
        code=code, code_system_uri=code_system, site=fromSite)

    
    # concept_with_fk = db.conceptForCode(codefk=fromCode_details['id'])
    concepts = db.conceptForCode(
        code=code, code_system=code_system, site=fromSite)

    if len(concepts) == 0:
        return "could not find a concept for this code: {}@{} for the site {}".format(code, code_system, fromSite), 404
    elif len(concepts) > 1:
        return "more than one possible match:\n" + "\n".join(concepts), 404
    else:
        # conceptfk, concept = concepts[0]
        concept = concepts[0]
        ans = db.list_all_mappings(site=toSite, concept=concept)

    fromCode_full_mapping = [e for e in db.mappings if e[h.SITE] == fromSite and e[h.CONCEPT]==concept]

    # add code_system data to each code
    for e in ans:
        e[h.SITE] = toSite
        o = db.code_details_with_site(
            code=e[h.CODE], code_system_uri=e[h.CODE_SYSTEM_URI], site=toSite)
        e[h.CODE_SYSTEM_URI] = o[h.CODE_SYSTEM_URI]
        e[h.CODE_SYSTEM_VERSION] = o[h.CODE_SYSTEM_VERSION]

    if not len(ans):
        return "no mapping found", 404
    else:
        # log.warning('oooooooooooooooo',fromCode_details)
        return (FHIR(concept=concept, sourceItem=fromCode_details,
                     targetItems=ans, sourceHasMultipleCorrespondingItems=len(fromCode_full_mapping)>1),
                200)


def set_mapping(o, o_old = None):
    """
    this removes the old corresponding mapping, and adds the new one(s)
    """
    if isinstance(o, list):
        return "tried to submit a list of mappings", 400
        # def f(a,b):
        #     return ( a[0]+b[0] , max(a[1],b[1]))
        # return reduce(f, map(set_mapping, o))
    else:
        try:
            # h.schema_mapping.validate(o)
            assert type(o) == Mapping
            assert o_old is None or type(o_old) == Mapping
        except Exception as e:
            log.warning(e)
            log.warning(f'wrong parameters {str(o)} {str(o_old)}')
            return return_missing_params
        
        o.equivalence = (
            h.EQUIVALENCE_EQUIVALENT
            if len(o.codes) == 1
            else h.EQUIVALENCE_NARROWER)
        
        ans = db.set_mapping(o)

        return ans, 200

def set_code_system(o):
    """
    set a code system
    must contains code system name and URI, version is optional
    """
    assert isinstance(o, CodeSystem)
    log.warning("<set code system {}>".format(o))
    ans = db.set_code_system(o)
    return ans, 200


def set_concept(o):
    """
    add a new concept
    """
    if not check_parameters(o[h.CONCEPT]):
        return return_missing_params
    log.warning("<set concept {}>".format(o))
    ans = db.set_concept(concept=o[h.CONCEPT])
    return ans, 200


def delete_concept(o):
    """
    remove a concept
    """
    if not check_parameters(o[h.CONCEPT]):
        return return_missing_params
    log.warning("<delete concept {}>".format(o))

    c = o[h.CONCEPT]
    if not c in db.concepts:
        log.warning(db.concepts)
        return 'no such concept', 400
    ans = db.delete_concept(concept=c)
    # also delete the corresponding mappings
    
    return ans, 200


def set_site(o):
    log.warning("todo")


def init():
    log.warning( f'running from {os.getcwd()}' )

    if not os.path.isfile(db.db_file):
        log.warning("No database file found at {}".format(db.db_file))
        h.printcolor("No database file found at {}".format(db.db_file),
                   color = h.bcolors.WARNING)
        db.create_database()
    else:
        log.warning("database file OK")
        h.printcolor("database file OK",
                     color = h.bcolors.OKGREEN)
        db.connect_database()
    db.init()
