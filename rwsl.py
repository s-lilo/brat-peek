"""
Read, write, save, load.
"""
import ann_structure

import csv
import pickle


# .ANN
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
def join_ann_files(doc_list, output_path):
    """
    Create a new .ann file in output_path with multiple annotations combined.
    WIP, I usually use it like this:
    corpus = ann_structure.AnnCorpus(in_path, txt=True)
    corpus.create_collections(['X', 'Y', 'Z'])
    for doc in [doc for doc in corpus.docs if doc.collection == 'X']:
        Y = corpus.get_doc_by_name(doc.name, 'Y')
        Z = corpus.get_doc_by_name(doc.name, 'Z')
        join_ann_files([doc, Y, Z], out_path)
        write_txt_file(doc, out_path)
    """
    new_doc = ann_structure.AnnSentence()
    current_t_id = 1
    for doc in doc_list:
        for ent in doc.anns['entities']:
            new_ent = ann_structure.Entity(name='T{}'.format(current_t_id), tag=ent.tag, span=ent.span,
                                           text=ent.text)
            new_doc.anns['entities'].append(new_ent)
            current_t_id += 1

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
        with open('{}/{}.ann'.format(output_path, doc.name), 'w') as f_out:
            for k in doc.anns:
                for ann in doc.anns[k]:
                    f_out.write(str(ann)+'\n')
                    tag = attribute_tuple[0]
                    if len(attribute_tuple) > 1:
                        arguments = [ann.name, attribute_tuple[1]]
                    else:
                        arguments = [ann.name]
                    f_out.write(str(ann_structure.Attribute(name='A{}'.format(ann.name[1:]),
                                                            tag=tag,
                                                            arguments=arguments))
                                + '\n')

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
        writer.writerow(["name", "path", "tag", "span", "text", "note"])
        for doc in corpus.docs:
            for ent in doc.anns['entities']:
                if ent.tag not in to_ignore:
                    if ent.notes:
                        writer.writerow([doc.name, doc.path, ent.tag, ent.span, ent.text, ent.notes[0].note])
                    else:
                        writer.writerow([doc.name, doc.path, ent.tag, ent.span, ent.text])

    print('Written tsv file to {}/{}.tsv'.format(output_path, corpus.name))


def print_tsv_from_text_freq(corpus, output_path, to_ignore=[]):
    """
    Create tsv file with unique text annotations and their frequency.
    Feed tags that you don't want to include with the to_ignore argument.
    :param corpus: AnnCorpus
    :param output_path: str
    :param to_ignore: list of str
    :return: writes tsv
    """
    with open('{}/{}_text_freq.tsv'.format(output_path, corpus.name), 'w') as f_out:
        writer = csv.writer(f_out, delimiter='\t')
        writer.writerow(["text", "frequency"])  # TODO: Add list of files column
        for cat in corpus.text_freq:
            if cat not in to_ignore:
                for txt in corpus.text_freq[cat]:
                    writer.writerow([txt, corpus.text_freq[cat][txt]])

    print('Written tsv file to {}/{}_text_freq.tsv'.format(output_path, corpus.name))


def print_tsv_for_norm(corpus, output_path, reference_tsv, to_ignore):
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
def separate_tags(corpus, folder_a, folder_b):
    """
    I created this function originally to separate the two axis of annotation in the MEDDOPROF corpus,
    which has tags like these: PACIENTE-PROFESION, SANITARIO-PROFESION, ...
    Output two new versions of each annotated file, one only with PACIENTE/SANITARIO/... tags
    and another with PROFESION...
    """
    for doc in corpus.docs:
        f_name = doc.name
        with open(folder_a + '/' + f_name + '.ann', 'w') as f_a:
            with open(folder_b + '/' + f_name + '.ann', 'w') as f_b:
                for ann in doc.anns['entities']:
                    axis_a = ann_structure.Entity(ann.name, ann.tag.split('-')[0], ann.span, ann.text)
                    f_a.write(str(axis_a) + '\n')
                    axis_b = ann_structure.Entity(ann.name, ann.tag.split('-')[1], ann.span, ann.text)
                    f_b.write(str(axis_b) + '\n')
