import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET
import cerberus
from collections import defaultdict
import re
import schema
SCHEMA = schema

austin = '/Users/cure51/Desktop/Udacity/austin_city_data.osm'
osm = '/Users/cure51/Desktop/Udacity/fake3.osm'

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons"]


mapping = { "St": "Street",
            "St.": "Street",
            "Ave": "Avenue",
            "Ave.": "Avenue",
            "Rd": "Road",
            "Rd.": "Road"
            }


def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)


def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


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


def update_name(name, mapping):
    objectpattern = street_type_re.search(name)
    string1 = objectpattern.group()

    if string1 in mapping.keys():
        newlength = len(name) - len(string1)
        newword = name[0:newlength]
        name = newword + mapping[string1]
        return name
    else:
        return name




NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')


# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp'] 
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    """splits up node children with ":" into key and type; if ":" is not found tag type is "regular." Specifically for "addr:street," the function also converts abbreviations for street, avenue, and road into the capitlazied full name. Also the function removes the 'tx' in the zipcode field. In addition, the function splits way children 'k' attribute as well and adds position for 'nd' child."""
    if element.tag == 'node':
        for item in NODE_FIELDS:
            try:
                node_attribs[item] = element.attrib[item]
            except:
                node_attribs[item] = "9999999"
        for child in element:
            node_tags_dict = {}
            node_tags_dict['id'] = element.attrib['id']
            node_tags_dict['value'] = child.attrib['v']
            if PROBLEMCHARS.match(child.attrib["k"]):
                continue
            elif LOWER_COLON.match(child.attrib["k"]):
                if (child.attrib['k'] == "addr:street"):
                    if street_type_re.search(child.attrib["k"]):
                        node_tags_dict['value'] = update_name(child.attrib['v'], mapping)
                        node_tags_dict['type'] =  child.attrib["k"].split(":",2)[0]
                        node_tags_dict['key'] = child.attrib["k"].split(":",1)[1]
                        tags.append(node_tags_dict)
                elif (child.attrib['k'] == "addr:postcode"):
                    if ("TX" or "tx" or "Tx") in child.attrib['v']:
                        node_tags_dict['value'] = child.attrib['v'][2:]
                        node_tags_dict['type'] =  child.attrib["k"].split(":",2)[0]
                        node_tags_dict['key'] = child.attrib["k"].split(":",1)[1]
                        tags.append(node_tags_dict)
                    else:
                        node_tags_dict['value'] = child.attrib['v']
                        node_tags_dict['type'] =  child.attrib["k"].split(":",2)[0]
                        node_tags_dict['key'] = child.attrib["k"].split(":",1)[1]
                        tags.append(node_tags_dict)
                else:
                    node_tags_dict['type'] =  child.attrib["k"].split(":",2)[0]
                    node_tags_dict['key'] = child.attrib["k"].split(":",1)[1]
                    tags.append(node_tags_dict)
            else:
                node_tags_dict["type"] = "regular"
                node_tags_dict["key"] = child.attrib["k"]
                tags.append(node_tags_dict)
        return {'node': node_attribs, 'node_tags': tags}

    elif element.tag == 'way':
        for item in WAY_FIELDS:
            try:
                way_attribs[item] = element.attrib[item]
            except:
                way_attribs[item] = "9999999"
                
        for field in WAY_FIELDS:
            way_attribs[field] = element.attrib[field]
            
        position = 0
        for child in element:
            if child.tag == 'tag':
                way_tags_dict = {}
                way_tags_dict['id'] = element.attrib['id']
                way_tags_dict['value'] = child.attrib['v']
                m = PROBLEMCHARS.match(child.attrib['k'])
                if m:
                    continue
                else:
                    if ':' in child.attrib['k']:
                        key_split = child.attrib['k'].split(":", 1)
                        way_tags_dict['type'] = key_split[0]
                        way_tags_dict['key'] = key_split[1]
                        tags.append(way_tags_dict)
                    else:
                        way_tags_dict['type'] = 'regular'
                        way_tags_dict['key'] = child.attrib['k']
                        tags.append(way_tags_dict)
        
            elif child.tag == 'nd':
                way_nodes_dict = {}
                way_nodes_dict['id'] = element.attrib['id']
                way_nodes_dict['node_id'] = child.attrib['ref']
                way_nodes_dict['position'] = position
                position += 1
                way_nodes.append(way_nodes_dict)
                    
                        
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}
# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


process_map(austin, validate=False)
