#!/usr/bin/env python3
from __future__ import print_function

import sys
import os
import logging
import pickle

logging.basicConfig(stream=sys.stdout, format="%(levelname)s: %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)

# used to load query result and do statistical stuff
def load_db(filename):
    filepath = "./policy/huawei/Huawei_Mate_20_OTA/db/saved_queries/"

    path = os.path.join(filepath, filename)

    try:
        with open(path, 'rb') as fp:
            retMe = pickle.load(fp)
        log.info("Loaded %d results from %s", len(retMe), filename)
        return retMe
    except IOError as e:
        log.error("Failed to load file: %s", e)
        return []

def id2name(id):
    inst_map_path = os.path.join("./policy/huawei/Huawei_Mate_20_OTA/db/", 'inst-map')
    retMe = []
    with open(inst_map_path, 'rb') as fp:
        node_id_map = pickle.load(fp)
        node_id_map_inv = dict([[v, k] for k, v in node_id_map.items()])

    for i in id:
        k = []
        for item in i:
            k.append(node_id_map_inv[item])
        retMe.append(k)
    return retMe

def main():
    # section 1

    # section 2
    # section2_analysis()
    # section 3
    section3_analysis()

def section1_analysis():
    return

def section2_analysis():
    print("-= section 2 part 1 =-")
    ids = load_db("analysis_of_a_privilege_escalation_1")
    names = id2name(ids)
    for k in names:
        if k[1].find("file") == -1 and k[2].find("file") == -1 and k[3].find("file") == -1:
            print(k)

    print("-= section 2 part 2 =-")
    ids = load_db("analysis_of_a_privilege_escalation_3")
    names = id2name(ids)
    for k in names:
        if k[0].startswith("file") == False:
            print(k)

    return

def section3_analysis():
    print("-= section 3 =-")
    ids = load_db("process_strength")
    names = id2name(ids)
    for k in names:
        print(k)
        if k[1].find("file") == -1:
            print(k)

    return

if __name__ == "__main__":
    sys.exit(main())
