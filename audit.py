import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

austin = '/Users/cure51/Desktop/Udacity/austin_city_data.osm'
osm = '/Users/cure51/Desktop/Udacity/fake3.osm'

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)


expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons"]

# UPDATE THIS VARIABLE
mapping = { "St": "Street",
            "St.": "Street",
            "Ave": "Avenue",
            "Ave.": "Avenue",
            "Rd": "Road",
            "Rd.": "Road"
            }

#searches street name for pattern and if true, and not in expected, adds it to dictionary
def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)

#tests to see if element tag is correct for purposes of auditing street types
def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

#main function for auditing street types
def audit(file_in):
    osm_f = open(file_in, "r")
    street_types = defaultdict(set)
    for elem in get_element(file_in):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_f.close()
    return street_types


'''''''Helper function for sample_data; uses root.clear to reduce in memory storage of city data.'''''''

def get_sample_elements(file_in, sample_size):
    context = ET.iterparse(file_in, events=('start', 'end'))
    _, root = next(context)
    count = 0
    for event, element in context:
        if event == 'end':
            yield element
            root.clear()
        count += 1
        if count > sample_size:
            break


"""Since the austin city data is too large to read into memory, this function returns a sample of parent elements and their attributes."""

def sample_data(file_in, sample_size):
    for element in get_sample_elements(file_in, sample_size):
            print element.tag,'='
            print element.attrib
            

"""Shows N lines of file"""
from itertools import islice
from pprint import pprint


def print_head(filename, N):
    with open(filename) as myfile:
        head = list(islice(myfile, N))
    pprint(head)
    
sample_data(austin, 600)
print_head(austin, 600)            
audit(austin)