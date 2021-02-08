"""
Read, write, save, load.
"""
import ann_structure

import csv


def print_tsv_from_corpus(corpus, output_path, to_ignore=[]):
    """
    Create tsv file with the corpus' text annotations.
    Feed tags that you don't want to include with the to_ignore argument.
    :param corpus: AnnCorpus
    :param output_path: str
    :param to_ignore: list of str
    :return: writes tsv
    """
    # TODO: Only prints entities
    with open(output_path + '/' + corpus.name + '.tsv', 'w') as f_out:
        writer = csv.writer(f_out, delimiter='\t')
        writer.writerow(["name", "path", "tag", "span", "text"])
        for doc in corpus.docs:
            for ent in doc.anns['entities']:
                if ent.tag not in to_ignore:
                    writer.writerow([doc.name, doc.path, ent.tag, ent.span, ent.text])


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

    with open(output_path + '/' + corpus.name + '.tsv', 'w') as f_out:
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


def separate_tags(corpus, folder_a, folder_b):
    """
    I created this function originally to separate the two axis of annotation in the MEDDOPROF corpus,
    which has tags like these: PACIENTE_PROFESION, SANITARIO_PROFESION, ...
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


if __name__ == "__main__":
    print_tsv_from_corpus()