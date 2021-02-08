'''
This script contains all annotation related objects.
There are three levels: corpus, document and annotation line.
Annotation lines can be of type: [Entity, Relation, Event, Attribute, Modification, Normalization, Note
and Placeholder].

More info about brat standoff format: http://brat.nlplab.org/standoff.html.
'''
import os
from collections import defaultdict, Counter
import glob
import random


# Corpus object (compilation of multiple AnnDocument)
class AnnCorpus:
    '''
    A corpus is a collection of documents.

    The input of object instances should always be a folder!
    Recursive by default. (TODO: Optional?)
    # TODO: iterable?
    '''
    def __init__(self, path):
        # Meta
        self.path = path
        self.name = os.path.split(path.rstrip('/'))[-1]  # corpus name is same as folder's
        # Content
        content = self._construct_corpus()
        self.docs = content
        # Stats
        count = self._count_corpus()
        self.count = count
        text_freq = self._text_frequency_corpus()
        self.text_freq = text_freq

    # Corpus construction
    def _construct_corpus(self):
        '''
        Get all .ann files in input folder and return a list of AnnDocuments.
        :return: list
        '''
        corpus = []
        for f in glob.iglob(os.path.join(self.path, '**/*.ann'), recursive=True):
            corpus.append(AnnDocument(f))
        
        return corpus

    # Corpus management
    # Retrieve collection of file from regex
    def get_collections(self, collections_set):
        '''
        A corpus may have different kind of texts, create collections to gather them.
        Use regex to find match inside folder/file name?
        :return:
        '''
        pass

    # Count
    def _count_corpus(self):
        '''
        Return sum of all counters
        :return:
        '''
        count = {}
        for doc in self.docs:
            for k in doc.count.keys():
                if k not in count.keys():
                    count[k] = doc.count[k]
                else:
                    count[k] += doc.count[k]

        return count

    def _text_frequency_corpus(self):
        '''
        Return sum of all text frequency counters.
        :return:
        '''
        count = {}
        for doc in self.docs:
            for k in doc.text_freq.keys():
                if k not in count.keys():
                    count[k] = doc.text_freq[k]
                else:
                    count[k] += doc.text_freq[k]

        return count

    # Document retrieval
    def get_doc(self, f_name):
        '''
        Returns a given doc in the corpus.
        TODO: allow for multiple docs?
        :return:
        '''
        return [doc for doc in self.docs if doc.name == f_name][0]

    def get_random_doc(self):
        """
        Returns a random document from the corpus!
        :return:
        """
        return self.docs[random.randint(0, len(self.docs)-1)]

    def get_all_text_from_tag(self, tag):
        all_text = []
        for doc in self.docs:
            all_text.extend(doc.get_text_from_tag(tag))

        return all_text

    def get_empty_files(self):
        '''
        Return which files have no annotations.
        A file should be empty if it has no TextBound annotations. (is this wrong?)
        '''
        return [doc.path for doc in self.docs if not doc.anns['entities']]


# Document object (compilation of lines of different tags)
class AnnDocument:
    '''
    A document is basically a container of smaller annotation atoms.

    The input of object instances should always be a .ann file!
    '''
    def __init__(self, path):
        # Meta
        self.path = path
        self.name = path.split('/')[-1][:-4]  # .ann ending not included in name
        # self.collection = ""  # Not implemented yet
        # Content
        content = self._construct_document()
        self.anns = content
        # Stats
        count = self._count_tags()
        self.count = count
        text_freq = self._text_frequency()
        self.text_freq = text_freq

    def __str__(self):
        # TODO: verbose and non-verbose? (don't print things that = 0)
        return self.name

    # Line understanding
    @staticmethod
    def _parse_line(line):
        '''
        Lines look like this:
        T2	Location 10 23	South America
        Separate each of its parts and return its corresponding object.
        :param line: str
        :return: annotation object
        '''
        line = line.rstrip()
        fields = line.split('\t')
        # Check type of annotation line
        if line.startswith('T'):  # TextBound: entities
            tag, span = fields[1].split()[0], fields[1].split()[1:]
            if len(span) == 3:  # Discontinuous annotations
                span = " ".join(span).split(';')
                span = [s.split(' ') for s in span]
                span = ((int(span[0][0]), int(span[0][1])), (int(span[1][0]), int(span[1][1])))
                return Entity(name=fields[0], tag=tag, span=span, text=fields[2])
            else:
                span = ((int(span[0]), int(span[1])),)
                return Entity(name=fields[0], tag=tag, span=span, text=fields[2])
        elif line.startswith('R'):  # Relations
            rel = fields[1].split(' ')
            return Relation(name=fields[0], tag=rel[0], arg1=rel[1], arg2=rel[2])
        elif line.startswith('E'):  # Events
            eve = fields[1].split(' ')
            return Event(name=fields[0], tag=eve[0].split(':')[0], trigger=eve[0].split(':')[1], arguments=eve[1:])
        elif line.startswith('A') or line.startswith('M'):  # Attributes
            # "For backward compatibility with existing standoff formats,
            # brat also recognizes the ID prefix "M" for attributes".
            att = fields[1].split(' ')
            return Attribute(name=fields[0], tag=att[0], arguments=att[1:])
        elif line.startswith('#'):  # Notes
            tag, ann_id = fields[1].split(' ')
            return Note(name=fields[0], tag=tag, ann_id=ann_id, note=fields[2])
        # TODO: read normalizations and placeholders

    # Object building
    def _construct_document(self):
        '''
        Open .ann file, read all lines and construct the document.
        :return: dict
        '''
        # Create dict with all of the file's content
        # TODO: implement normalizations and placeholders
        doc = {'entities': [], 'relations': [], 'events': [], 'attributes': [], 'notes': []}
        with open(self.path, 'r', encoding='utf-8') as f_in:
            for line in f_in:
                ann = self._parse_line(line)
                if isinstance(ann, Entity):
                    doc['entities'].append(ann)
                elif isinstance(ann, Relation):
                    doc['relations'].append(ann)
                elif isinstance(ann, Event):
                    doc['events'].append(ann)
                elif isinstance(ann, Attribute):
                    doc['attributes'].append(ann)
                elif isinstance(ann, Note):
                    doc['notes'].append(ann)

        # Get interactions between entities and other types
        for ent in doc['entities']:
            # Build relations
            for rel in doc['relations']:
                # Debería separar arg1 y arg2 pero ahora mismo no sé cuál es el mejor modo, TODO
                if rel.arg1.split(':')[-1] == ent.name:
                    ent.rels.append(rel)
                elif rel.arg2.split(':')[-1] == ent.name:
                    ent.rels.append(rel)
            # Build notes
            for note in doc['notes']:
                if note.ann_id == ent.name:
                    ent.notes.append(note)

        return doc

    # Count
    def _count_tags(self):
        '''
        Count all tags separated by type and return them in a dictionary.
        :return: dict
        '''
        tags_count = {}
        for k in self.anns.keys():
            tags = Counter()
            for a in self.anns[k]:
                tags.update([a.tag])
            tags_count[k] = tags

        return tags_count

    def get_text_from_tag(self, tag):
        doc_text = []
        for ent in self.anns['entities']:
            if ent.tag == tag:
                doc_text.append(ent.text)

        return doc_text

    # Text
    def _text_frequency(self):
        '''
        Get all text annotations and count them.
        :return: dict
        '''
        count = {}
        for ann in self.anns['entities']:
            if ann.tag not in count.keys():
                count[ann.tag] = Counter()
                count[ann.tag].update([ann.text])
            else:
                count[ann.tag].update([ann.text])

        return count
    # TODO: Return lowercased as option

    # Co-occurrence
    # Document wise?
    # Span wise?


# Annotation line atoms
# Entity (also called TextBound as they are the only ones that have text)
class Entity:
    def __init__(self, name: str, tag: str, span: tuple, text: str):
        self.name = name
        self.tag = tag
        self.span = span  # Spans are tuples with two tuples inside
        self.text = text
        # # Entity interactions:
        # # nested (elements that share part of span)
        # self.nested = []
        # # relations pointing to self
        self.rels = []
        # # events pointing to self
        self.events = []  # Separate triggers and arguments
        # # annotation's attributes
        self.attr = []
        # # annotator's notes
        self.notes = []

    def __repr__(self):
        if len(self.span) == 2:
            return '{}\t{} {} {};{} {}\t{}'.format(self.name, self.tag, self.span[0][0], self.span[0][1],
                                                   self.span[1][0], self.span[1][1], self.text)
        else:
            return '{}\t{} {} {}\t{}'.format(self.name, self.tag, self.span[0][0], self.span[0][1], self.text)

    def compare_overlap(self, other):
        """
        Compares span of two overlapping entities and returns info about the relative position.
        Five types of overlap:
              exact & nested-bigger & nested-smaller & starts-before & ends-after
        self:  []      [   ]              []            [   ]             [   ]
        other: []       []              [   ]             [   ]         [   ]

        # TODO: Discontinuous spans!!
        :param other: other Entity object.
        :return: string with overlap type.
        """
        if self.span[0][0] == other.span[0][0] and self.span[0][1] == other.span[0][1]:
            return "exact"
        elif self.span[0][0] <= other.span[0][0] and self.span[0][1] >= other.span[0][1]:
            return "nested-bigger"
        elif self.span[0][0] >= other.span[0][0] and self.span[0][1] <= other.span[0][1]:
            return "nested-smaller"
        elif self.span[0][0] <= other.span[0][0] <= self.span[0][1] <= other.span[0][1]:
            return "starts-before"
        elif other.span[0][0] <= self.span[0][0] <= other.span[0][1] <= self.span[0][1]:
            return "ends-after"
        else:
            return None


# Relation
class Relation:
    def __init__(self, name: str, tag: str, arg1: str, arg2: str):
        self.name = name
        self.tag = tag
        self.arg1 = arg1
        self.arg2 = arg2

    def __repr__(self):
        return '{}\t{} {} {}'.format(self.name, self.tag, self.arg1, self.arg2)


# Event
class Event:
    def __init__(self, name: str, tag: str, trigger: str, arguments: list):
        self.name = name
        self.tag = tag
        self.trigger = trigger
        self.arguments = arguments

    def __repr__(self):
        return '{}\t{}:{} {}'.format(self.name, self.tag, self.trigger, " ".join(self.arguments))


# Attributes and modifications
class Attribute:
    def __init__(self, name: str, tag: str, arguments: list):
        self.name = name
        self.tag = tag
        self.arguments = arguments
        self.type = self.check_type()

    def __repr__(self):
        return '{}\t{} {}'.format(self.name, self.tag, " ".join(self.arguments))

    def check_type(self):
        return 'binary' if len(self.arguments) == 1 else "multi-valued"


# Normalizations
# TODO: idk how this type works, check if parts are correct
class Normalization:
    def __init__(self, name, tag, referent, norm):
        self.name = name
        self.tag = tag
        self.referent = referent
        self.norm = norm


# Note
# TODO: Connect comments with their annotations somehow
class Note:
    def __init__(self, name: str, tag: str, ann_id: str, note: str):
        self.name = name
        self.tag = tag
        self.ann_id = ann_id
        self.note = note

    def __repr__(self):
        return "{}\t{} {}\t {}".format(self.name, self.tag, self.ann_id, self.note)


class Placeholder:
    pass


if __name__ == '__main__':
    pass
