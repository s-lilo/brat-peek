"""
Read, write, save, load.
"""
import ann_structure

import csv
import json
import pickle
import os


# .ANN
import peek

from ast import literal_eval


def write_ann_file(doc, output_path):
    """
    Create new .ann file in output_path with annotations in doc.
    """
    with open('{}/{}.ann'.format(output_path, doc.name), 'w') as f_out:
        for k in doc.anns:
            for ann in doc.anns[k]:
                f_out.write(str(ann)+'\n')

    print('Written ann file to {}/{}.ann'.format(output_path, doc.name))


# TODO: JOIN NON-TEXTBOUND
# TODO: AUTOMATIZE JOINING CORPORA
def join_ann_files(doc_list, output_path):
    """
    Create a new .ann file in output_path with multiple annotations combined.
    WIP, I usually use it like this:
    corpus = ann_structure.AnnCorpus(in_path, txt=True)
    corpus.create_collections_subfolders()
    for doc in [doc for doc in corpus.docs if doc.collection == 'X']:
        Y = corpus.get_doc_by_name(doc.name, 'Y')
        Z = corpus.get_doc_by_name(doc.name, 'Z')
        join_ann_files([doc, Y, Z], out_path)
        write_txt_file(doc, out_path)
    """
    new_doc = ann_structure.AnnSentence()
    # Textbound
    current_t_id = 1
    # Notes
    current_n_id = 1
    # Attributes
    current_a_id = 1
    # Relations
    current_r_id = 1
    for doc in doc_list:
        # Entities ID old to new mapping
        old_to_new_t_id = {}
        for ent in doc.anns['entities']:
            new_ent = ann_structure.Entity(name='T{}'.format(current_t_id), tag=ent.tag, span=ent.span,
                                           text=ent.text)
            new_doc.anns['entities'].append(new_ent)
            old_to_new_t_id[ent.name] = 'T{}'.format(current_t_id)
            if ent.notes:
                for note in ent.notes:
                    new_ent = ann_structure.Note(name='#{}'.format(current_n_id), tag=note.tag, ann_id='T{}'.format(current_t_id), note=note.note)
                    new_doc.anns['notes'].append(new_ent)
                    current_n_id += 1
            if ent.attr:
                for att in ent.attr:
                    new_ent = ann_structure.Attribute(name='A{}'.format(current_a_id), tag=att.tag, arguments=['T{}'.format(current_t_id)])
                    new_doc.anns['attributes'].append(new_ent)
                    current_a_id += 1
            current_t_id += 1

        if doc.anns['relations']:
            for rel in doc.anns['relations']:
                new_rel = ann_structure.Relation(name='R{}'.format(current_r_id), tag=rel.tag,
                                                 arg1='{}:{}'.format(rel.arg1.split(':')[0], old_to_new_t_id[rel.arg1.split(':')[1]]),
                                                 arg2='{}:{}'.format(rel.arg2.split(':')[0], old_to_new_t_id[rel.arg2.split(':')[1]]))
                new_doc.anns['relations'].append(new_rel)
                current_r_id += 1

    with open('{}/{}.ann'.format(output_path, doc_list[0].name), 'w') as f_out:
        for k in new_doc.anns:
            for ann in new_doc.anns[k]:
                f_out.write(str(ann)+'\n')

    print('Written ann file to {}/{}.ann'.format(output_path, doc_list[0].name))


def add_default_attribute(corpus, attribute_tuple, output_path):
    """
    The option to use default attributes in brat only applies to new annotations (as expected).
    This function adds a default attribute to existing .ann files for new layers of annotation.
    Attribute must be a tuple with two elements: tag and arguments
    """
    for doc in corpus.docs:
        new_doc = peek.AnnSentence()
        new_doc.name = doc.name

        if doc.anns["attributes"]:
            a_id = len(doc.anns["attributes"]) + 1
        else:
            a_id = 1

        for ann in doc.anns["entities"]:
            new_doc.copy_entity(ann)
            new_doc.from_entity(ann)
            tag = attribute_tuple[0]
            if len(attribute_tuple) > 1:
                arguments = [ann.name, attribute_tuple[1]]
            else:
                arguments = [ann.name]
            new_doc.anns["attributes"].append(ann_structure.Attribute(name='A{}'.format(a_id), tag=tag, arguments=arguments))
            a_id += 1

        write_ann_file(new_doc, output_path)
        print('Written ann file to {}/{}.ann'.format(output_path, doc.name))


# .TXT
def write_txt_file(doc, output_path):
    """
    Create new .txt file using txt attribute from doc
    """
    if doc.txt:
        with open('{}/{}.txt'.format(output_path, doc.name), 'w') as f_out:
            for sent in doc.txt:
                if sent != '\n':
                    f_out.write(sent + '\n')
                else:
                    f_out.write('\n')
            print('Written txt file to {}/{}.txt'.format(output_path, doc.name))
    else:
        print('Could not find text for doc {}'.format(doc.name))

def write_json_from_doc(doc, output_path, txt=False):
    """
    Create a JSON file that incorporates all annotations in the corpus and their related information.
    Optionally, include the text as another field.
    https://json-schema.org/understanding-json-schema/UnderstandingJSONSchema.pdf
    """
    json_dict = {"name": doc.name,
                 "annotations":
                     {ann.name: {"text": ann.text, "tag": ann.tag, "start_span": ann.span[0][0], "end_span": ann.span[0][1],
                                 # TOOD: Notes, attributes, relations
                                 "notes": {note.name: {"note": note.note} for note in ann.notes},
                                 "attributes": {att.name: {"type":att.type, "tag": att.tag,
                                                           "value":att.arguments[1] if att.type == 'multi-valued' else "True"}
                                                for att in ann.attr}
                                 }
                      for ann in doc.anns['entities']}}

    if txt:
        if doc.txt:
            json_dict["text"] = '\n'.join([sent for sent in doc.txt])
        else:
            print('AnnDoc object does not have an associated text')

    with open(output_path + '/{}.json'.format(doc.name), 'w') as f_out:
        json.dump(json_dict, f_out, indent=4, ensure_ascii=False)

def write_json_from_corpus(corpus, output_path, txt=False):
    """
    Create a JSON file that incorporates all annotations in the corpus and their related information.
    Optionally, include the text as another field.
    """
    json_dict = {}
    for doc in corpus.docs:
        doc_dict = {"name": doc.name,
                     "annotations":
                         {ann.name: {"text": ann.text, "tag": ann.tag, "start_span": ann.span[0][0],
                                     "end_span": ann.span[0][1],
                                     # TOOD: Notes, attributes, relations
                                     "notes": {note.name: {"note": note.note} for note in ann.notes},
                                     "attributes": {att.name: {"type": att.type, "tag": att.tag,
                                                               "value": att.arguments[1] if att.type == 'multi-valued'
                                                               else "True"} for att in ann.attr}
                                     }
                          for ann in doc.anns['entities']}}

        if txt:
            if doc.txt:
                doc_dict["text"] = '\n'.join([sent for sent in doc.txt])
            else:
                print('AnnDoc object does not have an associated text')

        json_dict[doc.name] = doc_dict

    with open(output_path + '/{}.json'.format(corpus.name), 'w') as f_out:
        json.dump(json_dict, f_out, indent=4, ensure_ascii=False)

def from_corpus_tsv_to_ann(tsv_path, output_path):
    """
    Create ann files from a tsv that contains all corpus information
    (like the file outputted by the function 'print_tsv_from_corpus')
    :param tsv_path: str with the path to the tsv file to use
    :param output_path: str with the folder where annotations will be saved
    """
    # Open TSV file
    with open(tsv_path, 'r') as f_in:
        tsv = csv.reader(f_in, delimiter='\t')
        # Skip header
        next(tsv)
        # Dictionary to put together annotations for same file (better to save it like this just in case the TSV file is not ordered)
        files_in_tsv = dict()
        # Go through each line, assume our TSV has the following fields: ["name", "tag", "span", "text", "note", "attributes"]
        for line in tsv:
            # Make sure file is in dict
            if not line[0] in files_in_tsv.keys():
                files_in_tsv[line[0]] = []
            files_in_tsv[line[0]].append(line[1:])
        # Go through each document, create annotations and store the .ann files

        for file in files_in_tsv.keys():
            new_doc = peek.AnnSentence()
            new_doc.name = file
            t_id = 1
            a_id = 1
            n_id = 1
            # New columns are "tag", "span", "text", "note", "attributes"
            for ann in files_in_tsv[file]:
                new_ent = peek.Entity(name='T{}'.format(t_id), tag=ann[0], span=literal_eval(ann[1]), text=ann[2])
                new_doc.anns['entities'].append(new_ent)
                if ann[3]:  # note
                    new_note = peek.Note(name='#{}'.format(n_id), tag='AnnotatorNotes', ann_id='T{}'.format(t_id), note=ann[3])
                    new_doc.anns['notes'].append(new_note)
                    n_id += 1
                if ann[4] and ann[4] != '[]':
                    att_line = ann[4].strip('[]').split(',')
                    for att in att_line:
                        old_att = peek.AnnSentence._parse_line(att.lstrip(' '))
                        new_args = ['T{}'.format(t_id)]
                        if len(old_att.arguments) == 2:
                            new_args.append(old_att.arguments[1])
                        new_att = peek.Attribute(name='A{}'.format(a_id), tag=old_att.tag, arguments=new_args)
                        new_doc.anns['attributes'].append(new_att)
                        a_id += 1
                t_id += 1
            write_ann_file(new_doc, output_path)


# TODO: I should modify the content of the tsv file to know where each annotation comes from, it might require some general rework of the text_freq attribute
# def from_freq_tsv_to_ann(tsv_path, output_path):
#     """
#     Create ann files from a tsv that contains the corpus' annotations grouped together by label and frequency
#     (like the file outputted by the function 'print_tsv_from_text_freq')
#     """
#     pass

# .TSV
def print_tsv_from_corpus(corpus, output_path, to_ignore=[]):
    """
    Create tsv file with all of the corpus' text annotations.
    Feed tags that you don't want to include with the to_ignore argument.
    :param corpus: AnnCorpus
    :param output_path: str
    :param to_ignore: list of str
    :return: writes tsv
    """
    # TODO: Only prints entities
    with open('{}/{}.tsv'.format(output_path, corpus.name), 'w') as f_out:
        writer = csv.writer(f_out, delimiter='\t')
        writer.writerow(["name", "tag", "span", "text", "note", "attributes"])
        for doc in corpus.docs:
            for ent in doc.anns['entities']:
                if ent.tag not in to_ignore:
                    # Print non-discontinuous annotations in a nicer way
                    if len(ent.span) == 1:
                        span = '{}, {}'.format(ent.span[0][0], ent.span[0][1])
                    fields = [doc.name, ent.tag, span, ent.text]
                    if ent.notes:
                        fields.append(ent.notes[0].note)
                    else:
                        fields.append('')
                    if ent.attr:
                        fields.append(ent.attr)
                    else:
                        fields.append('')
                    writer.writerow(fields)

    print('Written tsv file to {}/{}.tsv'.format(output_path, corpus.name))


def print_tsv_from_text_freq(corpus, output_path, lower=False, to_ignore=[]):
    """
    Create tsv file with unique text annotations and their frequency.
    Feed tags that you don't want to include with the to_ignore argument.
    :param corpus: AnnCorpus
    :param output_path: str
    :param lower: whether to use the lowercased text_freq or not
    :param to_ignore: list of str
    :return: writes tsv
    """
    with open('{}/{}_text_freq.tsv'.format(output_path, corpus.name), 'w') as f_out:
        writer = csv.writer(f_out, delimiter='\t')
        writer.writerow(["text", "label", "frequency"])  # TODO: Add list of files column
        if lower:
            for cat in corpus.text_freq_lower:
                if cat not in to_ignore:
                    for txt in corpus.text_freq_lower[cat]:
                        writer.writerow([txt, cat, corpus.text_freq_lower[cat][txt]])
        else:
            for cat in corpus.text_freq:
                if cat not in to_ignore:
                    for txt in corpus.text_freq[cat]:
                        writer.writerow([txt, cat, corpus.text_freq[cat][txt]])

    print('Written tsv file to {}/{}_text_freq.tsv'.format(output_path, corpus.name))


def print_tsv_for_norm(corpus, output_path, reference_tsv, to_ignore=[]):
    """
    Create tsv file with the corpus' text annotations with codes column for normalization.
    Can retrieve suggestions from tsv file using a reference file.
    Feed tags that you don't want to include with the to_ignore argument.
    :param corpus: AnnCorpus
    :param output_path: str
    :param reference_tsv: str
    :param to_ignore: list of str
    :return: writes tsv
    """
    # TODO: Only prints entities
    if reference_tsv:
        with open(reference_tsv, 'r') as f_in:
            reader = csv.reader(f_in, delimiter='\t')
            reader = list(reader)

    with open('{}/{}.tsv'.format(output_path, corpus.name), 'a') as f_out:
        writer = csv.writer(f_out, delimiter='\t')
        writer.writerow(["name", "path", "tag", "span", "text", "code"])
        for doc in corpus.docs:
            for ent in doc.anns['entities']:
                if ent.tag not in to_ignore:
                    found = False
                    if reference_tsv:
                        for row in reader:
                            if ent.text.lower() == row[-2].lower():
                                writer.writerow([doc.name, doc.path, ent.tag, ent.span, ent.text, row[-1]])
                                found = True
                                break
                        if not found:
                            writer.writerow([doc.name, doc.path, ent.tag, ent.span, ent.text])
                    else:
                        writer.writerow([doc.name, doc.path, ent.tag, ent.span, ent.text])

    print('Written tsv file to {}/{}.tsv'.format(output_path, corpus.name))


def print_tsv_for_notes():
    pass


def print_tsv_for_notes_unique(corpus, output_path):
    """Create TSV file with the unique annotations and their associated notes"""
    notes_dict = {}
    for label in corpus.text_labels:
        notes_dict[label] = {}

    for doc in corpus.docs:
        for ann in doc.anns['entities']:
            if ann.text not in notes_dict[ann.tag].keys() and ann.notes:
                notes_dict[ann.tag][ann.text] = ann.notes[0].note

    with open(output_path + '/corpus_unique_notes.tsv', 'w') as f_out:
        writer = csv.writer(f_out, delimiter='\t')
        for label in notes_dict:
            for ann in notes_dict[label]:
                writer.writerow([ann, label, notes_dict[label][ann]])


# PICKLE SAVE AND LOADING
def save_corpus(corpus, output_path: str):
    """
    Stores the information in an AnnCorpus object for later use.
    """
    with open(output_path + '/' + corpus.name + '.pckl', 'wb') as f_out:
        pickle.dump(corpus, f_out)
        print('Corpus stored at {}'.format(output_path + '/' + corpus.name + '.pckl'))


def load_corpus(input_path):
    """
    Loads pickled AnnCorpora.
    """
    with open(input_path, 'rb') as f_in:
        return pickle.load(f_in)


# OTHERS
def separate_tags(corpus, output_folder, include_empty=True):
    """
    Create new files to tags in different folders
    """
    # Create a folder for each tag
    for tag in corpus.text_labels:
        os.makedirs(output_folder + '/' + tag, exist_ok=True)
    # Go through each document
    for doc in corpus.docs:
        # Iterate through tags in corpus
        for tag in corpus.text_labels:
            # Create new document
            new_doc = ann_structure.AnnSentence()
            new_doc.name = doc.name
            # Get all annotations in document with our current tag
            anns = [ann for ann in doc.anns['entities'] if ann.tag == tag]
            # Stop here if the document has no annotations with this tag and include_empty is False
            if not anns and not include_empty:
                continue
            # Copy entities to our new document
            for ann in anns:
                new_doc.copy_entity(ann)
                new_doc.from_entity(ann)
            peek.rwsl.write_ann_file(new_doc, output_folder  + '/' + tag)