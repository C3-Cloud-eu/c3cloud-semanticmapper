from itertools import chain

def flatmap(f, items):
    return list(chain.from_iterable(map(f, items)))

# colored terminal output
class bcolors:
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def identity(x):
    return x
    
# helper function: print with a specified color
def printcolor(s, color, end='\n'):
    print(color, end='')
    print(s, end='')
    print(bcolors.ENDC, end=end)

def printinfo(s):
    printcolor(s, color=bcolors.OKBLUE)
def printok(s):
    printcolor(s, color=bcolors.OKGREEN)
def printwarn(s):
    printcolor(s, color=bcolors.WARNING)
def printerr(s):
    printcolor(s, color=bcolors.FAIL)

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


# ### requests ### #

# normalize and trim a string
# def clean(s):
#     if s is None:
#         return None
#     s = str(s)
#     if 'TBC by' in s:
#         s = ''
#     return(unicodedata.normalize('NFKC', str(s)).strip())

def group_by(l, key):
    keys = set([x[key] for x in l])
    return({x: [y for y in l if y[key] == x and len(y[CODE])] for x in keys})
