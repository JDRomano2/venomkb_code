#!/usr/bin/env python

from JDRBio import pubmed
import MySQLdb
import urllib2
import json
from pprint import pprint
import csv
from unidecode import unidecode 
import os.path

API_KEY = "99c093c1-75c8-4908-874d-22e71132282e"
REST_URL = 'http://data.bioontology.org'

venom_corpus = "|venom|snake venom|venoms|thrombin|fibrinogen|insulin|snake venoms|fibrin|toxic substance|formaldehyde|formalin|peptides|fibrinogen|glucagon|angiotensin ii|acetylcholinesterase|apoptosis|glucagon-like peptide-1 receptor|prothrombin|streptokinase|ion channels|toxins|carcinogens|gastrins|nadph oxidase|neurotensin|amylases|phosphotransferases|peroxidase|lipase|amylases|collagen|tissue plasminogen activator|cytokines|glucagon-like peptide 1|proton pumps|insulin receptor substrate proteins|calcium channels|gastrin-releasing peptide|actins|catalase|alanine transaminase|alkaline phosphatase|venom|insulin-like growth factor i|gelatinases|antibodies|lead|3f8 antibody|glycoproteins|complement system proteins|"

all_venoms = []
all_effects = []

def get_json(url):
    try:
        opener = urllib2.build_opener()
        opener.addheaders = [('Authorization', 'apikey token=' + API_KEY)]
        return json.loads(opener.open(url).read())
    except:
        print "There was an error retrieving the record. Skipping."
        pass

def print_annotations(annotations, get_class=True):
    all_annotations = []
    for result in annotations:
        #try:
        try:
            all_annotations.append(str(result["annotatedClass"]["prefLabel"]).lower())
        except UnicodeEncodeError:
            #all_annotations.append(unidecode(str(result["annotatedClass"]["prefLabel"]).lower()))
            print "There was an error with this record. Skipping..."
        #except:
        #    print "there was some kind of error."
        #    pass
    return list(set(all_annotations)) # 'uniq'-ify the list

def load_queries(filename):
    # Load queries with format 'pmid\tvenom\ttarget'
    input_records = [] # These each contain a line from the source file
    with open(filename) as tsv:
        for line in csv.reader(tsv, dialect="excel-tab"):
            input_records.append({'pmid': line[0], 'venom': line[1], 'effect': line[2]})
    return input_records

try:
    global db
    global cur
    db = MySQLdb.connect(read_default_file='~/.my.cnf', db='user_jdr2160')
    #table_name = 'literature_results'
    cur = db.cursor()

    # Load list of queries, then loop over the queries, passing into mysql and doing essentially the same thing
    # as the last loop, creating a new list of dicts for the results of the queries
    mysql_queries = load_queries("mysqlinput.txt")

    # Open output files if they exist, and store in appropriate structures, then delete the files
    if os.path.isfile("output_venoms.txt"):
        print("Venoms file found - picking up where we left off...\n")
        with open("output_venoms.txt") as venoms_file:
            all_venoms.extend([line.strip() for line in venoms_file])
            print(all_venoms)
    if os.path.isfile("output_effects.txt"):
        print("Effects file found - picking up where we left off...\n")
        with open("output_effects.txt") as effects_file:
            all_effects.extend([line.strip() for line in effects_file])
            print(all_effects)

    # MAKE SET OF PMIDS THAT ARE ALREADY USED
    print("Determining which pmids have already been used...")
    used_pmids = []
    ven_pmids = [ x.rsplit('|')[0] for x in all_venoms ]
    eff_pmids = [ y.rsplit('|')[0] for y in all_effects ]
    pmids_from_both = ven_pmids + eff_pmids
    used_pmids = list(set(pmids_from_both))
    print("...done!")
    print("------------------------------")
    
    # GET ALL PMIDS FROM articles_main TABLE
    pmids_list = []
    cur.execute("SELECT pmid FROM articles_main")
    all_pmids = cur.fetchall()
    for pmid in all_pmids:
        str_pmid = str(pmid[0])
        if str_pmid not in used_pmids:
            pmids_list.extend(pmid)
            #import pdb; pdb.set_trace()

    for a_query in pmids_list:
        print "Searching for PMID: {0}".format(a_query)
        cur.execute("SELECT * FROM articles_main WHERE pmid = '{0}'".format(a_query))
        venoms_entries = []
        effects_entries = []

        # Do some stuff with each record!
        # For annotator service: find each of
        # (1) "Amino Acid, Peptide, or Protein (T116)" - SNOMEDCT as ontology
        # (2) (something that represents action/target) (maybe: "organ or tissue function" T042
        record = {}
        row = cur.fetchone()
        pmid = str(row[0])
        medline_string = pubmed.get_medline([pmid])
        # If a search fails, try using a different method
        annotations_venom = get_json(REST_URL + "/annotator?include=prefLabel,synonym,definition&longest_only=true&ontologies=MESH,SNOMEDCT&semantic_types=T116&text=" + urllib2.quote(medline_string['AB']))
        #if len(annotations_venom) == 0:
        annotations_venom = annotations_venom + get_json(REST_URL + "/annotator?include=prefLabel,synonym,definition&longest_only=true&ontologies=MESH,SNOMEDCT&semantic_types=T131&text=" + urllib2.quote(medline_string['AB']))
        annotations_venom = annotations_venom + get_json(REST_URL + "/annotator?include=prefLabel,synonym,definition&longest_only=true&ontologies=SNOMEDCT&semantic_types=T011,T014,T204&text=" + urllib2.quote(medline_string['AB']))
        if len(annotations_venom) == 0:
            annotations_venom = get_json(REST_URL + "/annotator?include=prefLabel,synonym,definition&longest_only=true&ontologies=SNOMEDCT&semantic_types=T116,T123&text=" + urllib2.quote(medline_string['AB']))
        if len(annotations_venom) == 0:
            annotations_venom = get_json(REST_URL + "/annotator?include=prefLabel,synonym,definition&longest_only=true&semantic_types=T116,T123&text=" + urllib2.quote(medline_string['AB']))
        annotations_effect = get_json(REST_URL + "/annotator?include=prefLabel,synonym,definition&longest_only=true&ontologies=SNOMEDCT,WHO-ART&semantic_types=T033,T040,T042,T047,T055,T191&text=" + urllib2.quote(medline_string['AB']))

        print "\n=============================================================="
        print "\nPMID: " + pmid
        #print "\nPossible venoms: "
        venoms = print_annotations(annotations_venom)
        venoms = list(set(venoms)) # remove duplicates
        for j in venoms:
            if str(j) in venom_corpus: 
                print "Removing {0}".format(j)
                venoms.remove(j)
        #pprint(venoms)
        #print venoms

        #print "\nPossible effects: "
        effects = print_annotations(annotations_effect)
        #pprint(effects)

        if (len(venoms) > 0) and (len(effects) > 0):
            # Build rows to load into the tables
            # First table: venoms
            venoms_entries.extend( [ "{0}|{1}".format(pmid, y) for y in venoms ] )

            # Second table: effects
            effects_entries.extend( [ "{0}|{1}".format(pmid, x) for x in effects ] )
        else:
            venoms_entries.append("{0}|".format(pmid))
            effects_entries.append("{0}|".format(pmid))

        pprint(venoms_entries)
        pprint(effects_entries)

        '''
        # GET MANUAL RESULTS AND COMPARE
        print "\nManual Results:"
        print "Venom: {0}".format(str(row[1]))
        print "Effect: {0}".format(str(row[2]))
        '''

        all_venoms.extend(venoms_entries)
        all_effects.extend(effects_entries)

    print "All done!"


except MySQLdb.Error, e:
    print "You broke something."
    print "Error %d: %s" % (e.args[0],e.args[1])
    sys.exit(1)
finally:
    print "Cleaning up..."
    # SAVE RESULTS TO 2 DIFFERENT TEXT FILES
    # first: venoms
    with open("output_venoms.txt", "w") as venom_text_file:
        venom_text_file.write('\n'.join(all_venoms))
    # second: effects
    with open("output_effects.txt", "w") as effect_text_file:
        effect_text_file.write('\n'.join(all_effects))

    cur.close()
    db.commit()
    db.close()
