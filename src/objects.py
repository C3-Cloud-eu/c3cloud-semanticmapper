import json
import jsonpickle
from lib import identity

class Dictable():
    def from_dict(self, d):
        self.__dict__.update(d)
        return self
    def __repr__(self):
        return f'{str(type(self))}({self.tojson()}))'
    def tojson(self):
        return jsonpickle.encode(self, unpicklable=False)
    def __eq__(self, other):
        if type(self) != type(other) or set(self.__dict__.keys()) != set(other.__dict__.keys()):
            return False
        for e in self.__dict__.keys():
            if self.__dict__[e] != other.__dict__[e]:
                return False
        return True

class CodeSystem(Dictable):
    def __init__(self, code_system : str, uri : str):
        assert type(code_system) == str
        assert type(uri) == str

        self.code_system = code_system
        self.uri = uri
    def get_code_system(self):
        return self.code_system
    def get_uri(self):
        return self.uri
    

class Code(Dictable):
    def __init__(self, code : str, code_system : CodeSystem, designation : str):
        assert type(code) == str
        assert type(code_system) in [dict, CodeSystem]
        assert type(designation) == str
        
        self.code = code
        self.code_system = code_system if type(code_system) == CodeSystem else CodeSystem(**code_system)
        self.designation = designation
    def get_code(self):
        return self.code
    def get_code_system(self):
        return self.code_system
    def get_designation(self):
        return self.designation
    def from_dict(self, d):
        assert type(d['code_system']) in [dict, CodeSystem]
        self.code = d['code']
        self.code_system = (CodeSystem(**d['code_system']) if
                            type(d['code_system']) == dict else
                            d['code_system'])
        self.designation = d['designation']
        return self
    

class Mapping(Dictable):
    def __init__(self, concept : str,
                 site : str,
                 codes : [Code]
                 ):
        assert type(concept) == str
        assert type(site) == str
        assert all([type(e) in [dict, Code] for e in codes])

        self.codes = [Code(**c) if type(c) == dict else c for c in codes]
        # print('$$$$$$$$$$$$$$$$$$$$$$$$ creating mapping $$$$$$$$$$$$$$$$$$$$$')
        # print(self.codes)
        # print('>>>>>>>>>>>>>>>>>>>>>>>>')
        # assert(all([type(e) == Code for e in self.codes]))

        self.concept = concept
        self.site = site
        # self.codes = codes
    def get_concept(self):
        return self.concept
    def get_site(self):
        return self.site
    def get_codes(self):
        return self.codes
    def from_dict(self, d):
        assert all([type(e) in [dict, Code] for e in  d['codes']])
        self.concept = d['concept']
        def f(e):
            return Code(**e) if(type(e) == dict) else e
                
        self.codes = [f(e) for e in d['codes']]
        self.site = d['site']
        return self
    
    
