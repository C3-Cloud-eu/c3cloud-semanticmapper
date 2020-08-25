########
# FHIR #
########

import helpers as h
import db
from itertools import groupby
import logging



# builds the FHIR response
def FHIR(concept, sourceItem, targetItems, sourceHasMultipleCorrespondingItems=False):
    log = logging.getLogger('service')

    csa = sourceItem[h.CODE_SYSTEM]

    def build_group_element(code_list):
        # log.warning('++++++++++++++++++++++++++++')
        # log.warning(code_list)
        assert(len(list(set( e[h.CODE_SYSTEM] for e in code_list))) == 1)
        csb = code_list[0][h.CODE_SYSTEM]
    
        if csa == csb:
            equiv = h.EQUIVALENCE_EQUAL
        else:
            if len(code_list) > 1:
                if sourceHasMultipleCorrespondingItems:
                    equiv = h.EQUIVALENCE_RELATED_TO
                else:
                    equiv = h.EQUIVALENCE_NARROWER
            else:
                if sourceHasMultipleCorrespondingItems:
                    equiv = h.EQUIVALENCE_WIDER
                else:
                    equiv = h.EQUIVALENCE_EQUIVALENT
    
        targets = [{
            'code': t[h.CODE],
            'display': t[h.DESIGNATION],
            'equivalence': equiv,
            'comment': db.equivalences[equiv]
        } for t in code_list]

    
    
        element = {
            'code': sourceItem[h.CODE],
            'display': sourceItem[h.DESIGNATION],
            'target': targets
        }
    
        return {
                'source': sourceItem[h.CODE_SYSTEM_URI],
                'sourceVersion': sourceItem[h.CODE_SYSTEM_VERSION],
                'target': code_list[0][h.CODE_SYSTEM_URI],
                'targetVersion': targetItems[0][h.CODE_SYSTEM_VERSION],
                'element': element
                }
    
    ## mappedlist = [build_group_element(i for i in targetItems if i[h.CODE_SYSTEM]==e) for e in set()]
    mappedlist = [build_group_element(list(e)) for _, e in groupby(targetItems, lambda x: x[h.CODE_SYSTEM])]

    target_cs_pretty = ','.join( set(sorted([e[h.CODE_SYSTEM] for e in targetItems])) )
    
    res = {
        'resourceType': "ConceptMap",
        'title': "mapping of '{}' from {} to {}".format(
            concept,
            "{} ({})".format(sourceItem[h.SITE], sourceItem[h.CODE_SYSTEM]),
            "{} ({})".format(targetItems[0][h.SITE], target_cs_pretty)), ## targetItems[0][h.CODE_SYSTEM])),
        'group': mappedlist
        # # debug
        # , 'concept': concept,
        # 'source': sourceItem,
        # 'targets': targetItems
    }
    # print(res)
    return(res)
