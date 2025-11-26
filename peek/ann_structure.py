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
import copy


# Corpus object (compilation of multiple AnnDocument)
class AnnCorpus:
    '''
    A corpus is a collection of documents.

    The input of object instances should always be a folder!
    Recursive by default. (TODO: Optional?)
    # TODO: iterable?
    '''

    def __init__(self, path, txt=False, from_list=False):
        # Meta
        self.path = path
        self.name = os.path.split(path.rstrip('/'))[-1]  # corpus name is same as folder's
        # Content
        if from_list:
            content = from_list
            # From list usage:
            # corpus = AnnCorpus(path='', from_list=[list,with,AnnDocs])
        else:
            content = self._construct_corpus(txt)
        self.docs = content
        self.collections = set()
        # Stats
        count = self._count_corpus()
        self.count = count
        self.text_freq = self._text_frequency_corpus()
        self.text_freq_lower = self._text_frequency_corpus(lower=True)
        # Labels found in the corpus
        self.text_labels = sorted(list(set([ent for ent in self.count['entities']])))
        self.rel_labels = sorted(list(set([ent for ent in self.count['relations']])))
        self.event_labels = sorted(list(set([ent for ent in self.count['events']])))
        self.attr_labels = sorted(list(set([ent for ent in self.count['attributes']])))

    def __len__(self):
        # Returns the number of documents in the corpus
        return len(self.docs)

    # Corpus construction
    def _construct_corpus(self, with_text=False):
        '''
        Get all .ann files in input folder and return a list of AnnDocuments.
        :return: list
        '''
        corpus = []
        for f in glob.iglob(os.path.join(self.path, '**/*.ann'), recursive=True):
            corpus.append(AnnDocument(f, txt=with_text))

        return corpus

    # Corpus management
    # We might have different types of documents, or even the same documents annotated with multiple systems
    # Collections are a way to group documents within the same folder
    # Three ways to do it:
    # 1. If you have your documents in separate folders, this will retrieve it from the document's path
    # and use its name as the collection
    def create_collections_subfolders(self):
        '''
        A corpus may have different types of texts or even the same texts annotated separated in subfolders.
        This function automatically creates collections using the name of each file's folder.
        :return:
        '''
        counter = defaultdict(int)
        for doc in self.docs:
            collection = doc.path.split('/')[-2]
            doc.collection = collection
            counter[collection] += 1
            self.collections.update([collection])
        print('Collections assigned:\n{}'.format('\n'.join(['{}: {}'.format(c, counter[c]) for c in counter])))

    # 2. Use a list of possible collections
    def create_collections_list(self, collections_set):
        counter = []
        collections_list = list(collections_set)
        collections_list.sort(key=len, reverse=True)
        for collection in collections_list:
            d = 0
            for doc in self.docs:
                # if collection in doc.path.split('/')[:-1]:
                if not doc.collection:
                    if collection in doc.path:
                        doc.collection = collection
                        d += 1
            counter.append(d)
            self.collections.update([collection])
        print('Collections assigned:\n{}'.format('\n'.join([str(z) for z in zip(collections_list, counter)])))

    # 3. Use a regular expression to look for a pattern inside the file's path
    # TODO: This would be the general logic, need to fix, allow flags, etc.
    # def create_collections_regex(self, re):
    #     counter = defaultdict(int)
    #     for doc in self.docs:
    #         if regex.match(re, doc.path):
    #             collection = re
    #             doc.collection = collection
    #             counter[collection] += 1
    #             self.collections.update([collection])
    #     print('Collections assigned:\n{}'.format('\n'.join(['{}: {}'.format(c, counter[c]) for c in counter])))

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
                    count[k] = Counter()
                count[k] += doc.count[k]

        return count

    def _text_frequency_corpus(self, lower=False):
        '''
        Return sum of all text frequency counters.
        :return:
        '''
        count = {}
        for doc in self.docs:
            if lower:
                for k in doc.text_freq_lower.keys():
                    if k not in count.keys():
                        count[k] = Counter()
                    count[k] += doc.text_freq_lower[k]
            else:
                for k in doc.text_freq.keys():
                    if k not in count.keys():
                        count[k] = Counter()
                    count[k] += doc.text_freq[k]

        return count

    # Document retrieval
    def get_doc_by_name(self, f_name, collection=''):
        """
        Returns a given doc in the corpus.
        TODO: allow for multiple docs?
        :return:
        """
        try:
            if collection:
                return [doc for doc in self.docs if doc.name == f_name and doc.collection == collection][0]
            else:
                return [doc for doc in self.docs if doc.name == f_name][0]
        except IndexError:
            print('File not in corpus')

    def get_random_doc(self):
        """
        Returns a random document from the corpus!
        :return:
        """
        return self.docs[random.randint(0, len(self.docs) - 1)]

    def get_text_from_tag(self, tag):
        all_text = []
        for doc in self.docs:
            all_text.extend(doc.get_text_from_tag(tag))

        return all_text

    def get_empty_files(self):
        """
        Return which files have no annotations.
        A file should be empty if it has no TextBound annotations.
        """
        return [doc.path for doc in self.docs if not doc.anns['entities']]


# Document object (compilation of lines of different tags)
class AnnDocument:
    """
    A document is basically a container of smaller annotation atoms.

    The input of object instances should always be a .ann file!
    """

    def __init__(self, path, txt=False):
        # Meta
        self.path = path
        self.name = path.split('/')[-1][:-4]  # .ann ending not included in name
        self.collection = ''
        # Content
        content = self._construct_document()
        self.anns = content
        # Text files  ** This is experimental, might take a while to load big corpora **
        if txt:
            try:
                with open(self.path[:-3] + 'txt', 'r') as doc_txt:
                    #self.txt = [sent.rstrip('\n') if sent != '\n' else sent for sent in doc_txt.readlines()]
                    self.txt = [sent.rstrip('\n') for sent in doc_txt.readlines()]
                    # To get the entire text as a string, you can join all items in the list using '\n'.join(doc.txt)
                    # I know this is weird but it's a workaround for files with multiple newlines together
            except FileNotFoundError:
                print('Text file for <{}> not found!'.format(self.path))
                self.txt = []
        else:
            self.txt = []
        # Stats
        self.count = self._count_tags()
        self.text_freq = self._text_frequency()
        self.text_freq_lower = self._text_frequency(lower=True)

    def __str__(self):
        # TODO: verbose and non-verbose? (don't print things that = 0)
        return self.name

    def __repr__(self):
        # TODO: verbose and non-verbose? (don't print things that = 0)
        return self.name

    def __contains__(self, item):
        # Returns whether a given annotation is equal to another annotation within the document
        return any([item == ann for ann in self.anns['entities']])

    # Line understanding
    @staticmethod
    def _parse_line(line):
        """
        Lines look like this:
        T2	Location 10 23	South America
        Separate each of its parts and return its corresponding object.
        :param line: str
        :return: annotation object
        """
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
            if len(fields) > 2:
                return Note(name=fields[0], tag=tag, ann_id=ann_id, note=fields[2])
            else:
                return Note(name=fields[0], tag=tag, ann_id=ann_id, note="")
        # TODO: read normalizations and placeholders

    # Object building
    def _construct_document(self):
        """
        Open .ann file, read all lines and construct the document.
        :return: dict
        """
        # Create dict with all of the file's content
        # TODO: implement normalizations and placeholders
        doc = {'entities': [], 'relations': [], 'events': [], 'attributes': [], 'notes': []}
        with open(self.path, 'r', encoding='utf-8') as f_in:
            for line in f_in:
                try:
                    ann = self._parse_line(line)
                except IndexError:
                    print(
                        'File {} seems to be faulty, please check and load the corpus again. Ignoring wrongly-formatted line for now...'.format(
                            self.path))
                    continue

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
                else:
                    print('Could not recognize the following line in file {}, please check:\n{}\n'.format(self.path,
                                                                                                          line))

        # Get interactions between entities and other types
        for ent in doc['entities']:
            # Build relations
            for rel in doc['relations']:
                # Debería separar arg1 y arg2 pero ahora mismo no sé cuál es el mejor modo, TODO
                if rel.arg1.split(':')[-1] == ent.name:
                    ent.rels.append(rel)
                elif rel.arg2.split(':')[-1] == ent.name:
                    ent.rels.append(rel)
            # Build attributes
            for att in doc['attributes']:
                if att.arguments[0] == ent.name:
                    ent.attr.append(att)
            # Build notes
            for note in doc['notes']:
                if note.ann_id == ent.name:
                    ent.notes.append(note)

        return doc

    # Count
    def _count_tags(self):
        """
        Count all tags separated by type and return them in a dictionary.
        :return: dict
        """
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
    def _text_frequency(self, lower=False):
        """
        Get all text annotations and count them.
        :return: dict
        """
        count = {}
        for ann in self.anns['entities']:
            if ann.tag not in count.keys():
                count[ann.tag] = Counter()
            if lower:
                count[ann.tag].update([ann.text.lower()])
            else:
                count[ann.tag].update([ann.text])

        return count

    # Co-occurrence
    # Document wise?
    # Span wise?


class AnnSentence(AnnDocument):
    """
    A sentence is a special kind of AnnDocument that is fed metadata, annotations and text manually.
    """

    def __init__(self, name='new_doc'):
        # Meta
        self.path = ""
        self.name = name
        self.source = ""
        # Content
        self.anns = {'entities': [], 'relations': [], 'events': [], 'attributes': [], 'notes': []}
        # Text files  ** This is experimental, might take a while to load big corpora **
        self.txt = []
        # Stats
        self.count = self._count_tags()
        self.text_freq = self._text_frequency()
        self.text_freq_lower = self._text_frequency(lower=True)

    def update_stats(self):
        """
        Stats items should be updated after adding new ones
        """
        self.count = self._count_tags()
        self.text_freq = self._text_frequency()

    def copy_entity(self, ent):
        """
        Copy a textbound entity
        We'll need to use deepcopy to create a separate object that won't change the original
        """
        self.anns['entities'].append(copy.deepcopy(ent))

    def from_entity(self, ent):
        """
        Copy an entity's interactions (relations, events, attributes, ... pointing to it)
        """
        if ent.rels:
            self.anns['relations'].extend(copy.deepcopy(ent.rels))
        if ent.events:
            self.anns['events'].extend(copy.deepcopy(ent.events))
        if ent.attr:
            self.anns['attributes'].extend(copy.deepcopy(ent.attr))
        if ent.notes:
            self.anns['notes'].extend(copy.deepcopy(ent.notes))

    def copy_doc(self, doc):
        """
        Copy all annotations from a given AnnDocument
        """
        for ann in doc.anns['entities']:
            self.copy_entity(ann)
            self.from_entity(ann)


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

    def __eq__(self, other):
        # A text-bound entity is the same as another if it has the same text, the same tag and the same span
        return (self.text == other.text) and (self.tag == other.tag) and (self.span == other.span)

    def __contains__(self, item):
        # Whether a given text is in an annotation
        return item in self.text

    def compare_overlap(self, other):
        """
        Compares span of two overlapping entities and returns info about the relative position.
        Five types of overlap:
              exact & nested-bigger & nested-smaller & starts-before & ends-after
        self:  []      [   ]              []            [   ]             [   ]
        other: []       []              [   ]             [   ]         [   ]

        # TODO: Discontinuous spans!!
        # TODO possible bug? Contiguous annotations are considered overlaps with the rules below, this should not be the case
        # (e.g. if an annotation ends at ch 170 (not included in the actual text) and another starts at ch 170 (this time included in the text))
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
        # Binary attributes only have one possible argument: its associated entity
        # Multi-valued attributes have another argument on top of the associated entity: the attribute subtype
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
class Note:
    def __init__(self, name: str, tag: str, ann_id: str, note: str):
        self.name = name
        self.tag = tag
        self.ann_id = ann_id
        self.note = note

    def __repr__(self):
        return "{}\t{} {}\t{}".format(self.name, self.tag, self.ann_id, self.note)


class Placeholder:
    pass
