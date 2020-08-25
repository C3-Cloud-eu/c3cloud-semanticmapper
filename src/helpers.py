import csv
from schema import Schema, And, Use, Optional

# constants

SITE = 'site'
CODE_SYSTEM = 'code_system'
CODE_SYSTEM_URI = 'code_system_uri'
CODE_SYSTEM_VERSION = 'code_system_version'
CODE = 'code'
DESIGNATION = 'designation'
CONCEPT = 'concept'
EQUIVALENCE = 'equivalence'
EQUIVALENCE_DEFINITION = 'equivalence_definition'

EQUIVALENCE_DISJOINT = 'Disjoint'
EQUIVALENCE_EQUAL = 'Equal'
EQUIVALENCE_EQUIVALENT = 'Equivalent'
EQUIVALENCE_INEXACT = 'Inexact'
EQUIVALENCE_NARROWER = 'Narrower'
EQUIVALENCE_RELATED_TO = 'Related To'
EQUIVALENCE_SPECIALIZES = 'Specializes'
EQUIVALENCE_SUBSUMES = 'Subsumes'
EQUIVALENCE_UNMATCHED = 'Unmatched'
EQUIVALENCE_WIDER = 'Wider'


column_list = [CONCEPT, SITE, CODE_SYSTEM,
               CODE, DESIGNATION]  # TODO add EQUIVALENCE


schema_mapping = Schema({
    'concept': And(str, len),
    'site': And(str, len),
    'codes': [{'code': And(str, len),
               'code_system': And(str, len),
               'code_system_uri': And(str, len),
               'designation': And(str, len)}]
})

# schema_mapping = {
#     'concept': 'string',
#     'site': 'string',
#     'codes': [{'code': 'string',
#                'code_system': 'string',
#                'code_system_uri': 'string',
#                'designation': 'string'}]
# }



####################
# helper functions #
####################


def dictFromKeyValues(keys, values):
    return {k: v for k, v in zip(keys, values)}


def load_csv(filename):
    with open(filename, 'r') as f:
        r = csv.reader(f)
        table = [row for row in r]
    return table

# creates a csv file from a list of dicts [{k:v,...}]
# where each key is the column name


def save_csv(filename, dicts):
    with open(filename, 'w', newline='') as f:
        w = csv.writer(f, delimiter=',', quotechar='"')
        columns = dicts[0].keys()
        w.writerow(columns)
        for r in dicts:
            w.writerow(r.values())


# reads a csv with headers and turns it to a dict of dicts
# the first column shall be the id (used as keys)
def csv_to_documents(filename):
    l = load_csv(filename)
    headers = l[0][1:]
    body = l[1:]
    return {r[0]: {k: v for k, v in zip(headers, r[1:])} for r in body}


def build_item(site="", code_system="", code="", designation="", concept=""):
    return {SITE:        site,
            CODE_SYSTEM: code_system,
            CODE:        code,
            DESIGNATION: designation,
            CONCEPT:     concept}


# colored terminal output
class bcolors:
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


# helper function: print with a specified color
def printcolor(s, color, end='\n'):
    print(color, end='')
    print(s, end='')
    print(bcolors.ENDC, end=end)
