"""
Read corpus text for different purposes.
"""
import ann_structure

import csv
import re

import peek

import rwsl


# This will save us from writing lots of redundant code
def txt_wrapper(f):
    '''
    Decorator to check whether an AnnDocument object has a text attribute associated.
    '''
    def check_txt(doc, *args, **kwargs):
        if doc.txt != '':
            return f(doc, *args, **kwargs)
        else:
            print('Text file for <{}> not found!'.format(doc.path))
    return check_txt


@txt_wrapper
def check_annotations_alignment_doc(doc):
    """
    # TODO: Needs more testing, I think there might be some strange behaviour
    Check whether the annotations in a document are properly aligned at span level and can be properly shown by brat.
    """
    full_txt = '\n'.join(doc.txt)
    misalignment = False
    for ann in doc.anns['entities']:
        if ann.text != full_txt[ann.span[0][0]:ann.span[0][1]]:
            print('ANNOTATION NOT ALIGNED: ', ann.text, '|', doc.name)
            misalignment = True
    return misalignment


def check_annotations_alignment_corpus(corpus):
    """
    # TODO: Needs more testing, I think there might be some strange behaviour at doc level
    Check whether the annotations in a document are properly aligned at span level and can be properly shown by brat.
    """
    misaligned_list = []
    for doc in corpus.docs:
        if check_annotations_alignment_doc(doc):
            misaligned_list.append(doc.name)

    if not misaligned_list:
        print('No annotations misaligned in corpus!')
    else:
        print('Some annotations are misaligned! Please check the following files:')
        print(misaligned_list)
    return misaligned_list

@txt_wrapper
def doc2sent(doc: ann_structure.AnnDocument, tokenizer=''):
    '''
    Separate a document into sentences and return its corresponding annotations after adjusting their span.
    :param doc: AnnDocument
    :param tokenizer: language for sent_tokenize if you want to use it
    # TODO: Discontinuous spans
    '''
    # Tokenize
    sents = doc.txt
    # NLTK tokenizer deletes trailing whitespaces, which messes up spans. Need an alternative!
    # if tokenizer:
    #     sents = sent_tokenize(''.join(sents), language=tokenizer)
    # Span counters:
    current_span = 0
    # Save new sentences
    sent_list = []
    # Iterate through sentences
    for i, sent in enumerate(sents):
        ann_sent = ann_structure.AnnSentence()
        ann_sent.path = doc.path
        ann_sent.name = '{}_sent{}'.format(doc.name, i+1)
        ann_sent.txt.append(sent)
        # Get sentence spans
        if sent != '\n':
            ending_span = current_span + len(sent)
        else:
            # Brat doesn't count newlines. If we add them to our ending span, we'll be off by one ch for every newline.
            ending_span = current_span
        # Get annotations for the sentence
        for ent in doc.anns['entities']:
            # If the annotation's span is inside the sentence's, construct a new entity
            if ent.span[0][0] >= current_span and ent.span[0][1] <= ending_span:
                new_start_span = ent.span[0][0] - current_span
                new_end_span = ent.span[0][1] - current_span
                new_ent = ann_structure.Entity(name=ent.name, tag=ent.tag, span=((new_start_span, new_end_span),),
                                               text=ent.text)
                ann_sent.anns['entities'].append(new_ent)
                ann_sent.from_entity(ent)
        current_span = ending_span + 1
        ann_sent.update_stats()
        sent_list.append(ann_sent)

    return sent_list


def sent2doc(sent_list):
    """
    Given a list of AnnSentences, merge them into a single document.
    """
    # This will be the final document.
    ann_sent = ann_structure.AnnSentence()
    ann_sent.name = 'new_doc_clinic'
    # We will need to take these into account. If we repeat IDs, our new file won't be read properly.
    last_t_id = 1
    # Span counters
    current_span = 0
    for sent in sent_list:
        # Retrieve text
        ann_sent.txt += ''.join(sent.txt) + '\n'
        # Adapt entity's id but also rels, events, ....
        for ent in sent.anns['entities']:
            # Set new name for each entity
            new_name = 'T{}'.format(last_t_id)
            # Update counter
            last_t_id += 1
            # Adjust spans...
            new_start_span = ent.span[0][0] + current_span
            new_end_span = ent.span[0][1] + current_span
            # Create and append resulting entity
            new_ent = ann_structure.Entity(name=new_name, tag=ent.tag, span=((new_start_span, new_end_span),),
                                           text=ent.text)
            ann_sent.anns['entities'].append(new_ent)
            # TODO: Include non-textbound annotations.
        # Update spans...
        current_span += len(sent.txt) + 1
    return ann_sent


@txt_wrapper
def get_text_window(doc: ann_structure.AnnDocument, annotation, size=75, direction="lr", include_mention=True):
    """
    Get context for a given annotation by retrieving the text beside it.
    doc: AnnDocument the annotation belongs to, loaded with txt=True
    ann: Entity object
    size: number of characters to include in the text window
    direction: sides to include in the text window (either l for left, r for right, or lr for both)
    include_mention: whether to include the mention text in the output string (surrounded by a double pipe character || to distinguish it)
    """
    # Get text
    txt = '\n'.join([sent for sent in doc.txt])
    # Get left and right windows

    # Create string
    output_string = ''
    if 'l' in direction:
        l_slice = int(annotation.span[0][0]) - int(size)
        if l_slice < 0:
            l_slice = 0
        l = txt[l_slice:int(annotation.span[0][0])]
        output_string += l
    if include_mention:
        output_string += '||{}||'.format(annotation.text)
    if 'r' in direction:
        r_slice = int(annotation.span[0][1]) + int(size)
        if r_slice > len(txt):
            r_slice = len(txt)
        r = txt[int(annotation.span[0][1]):r_slice]
        output_string += r

    return output_string


def annotation_density(corpus):
    # 1. Doc length
    ch_len = []
    tok_len = []
    # 2. Earliest and latest annotation point (absolute/relative)
    starting_point_ch = []   # list of tuples with (position, doc_len)
    starting_point_tok = []
    relative_starting_point = []
    ending_point_ch = []
    ending_point_tok = []
    relative_ending_point = []
    # 3.
    pass
    # TODO: Finish this


@txt_wrapper
def generate_suggestion_re(doc, word_dict, flags=[]):
    """
    Look up a dict of words or expressions in a document to suggest new textbound annotations.
    The dict must have the text to look up as key and a tuple inside: class and comment (to be added to brat's comment field, e.g. for codification - can be empty)

    """
    new_doc = ann_structure.AnnSentence()
    new_doc.name = doc.name
    # Create big regex
    rgx = '(?![^\W_])|'.join([re.escape(w) for w in word_dict.keys()])
    # Current span
    s_id = 0
    # If the given doc already has annotations, copy them to our new doc and ontinue from the last id.
    # Otherwise, start from 1.
    if doc.anns['entities']:
        new_doc.copy_doc(doc)
        T_id = max([int(ent.name[1:]) for ent in doc.anns['entities']]) + 1
        N_id = max([int(ent.name[1:]) for ent in doc.anns['notes']]) + 1
    else:
        T_id = 1
        N_id = 1
    p = re.compile(rgx, re.IGNORECASE)
    total_sugs = 0
    for i, sent in enumerate(doc.txt):
        # Try to match our patterns in each sentence
        matches = p.finditer(sent)
        if matches:
            # Create annotations for every match
            for match in matches:
                total_sugs += 1
                ent_s_span = match.span()[0] + s_id
                end_e_span = match.span()[1] + s_id
                new_ent = peek.Entity(name='T{}'.format(T_id),
                                      tag='_SUG_' + word_dict[match.group().lower()][0],
                                      text=match.group(),
                                      span=((ent_s_span, end_e_span),))
                if word_dict[match.group().lower()][1] != '':
                    new_note = peek.Note(name='#{}'.format(T_id),
                                         tag='AnnotatorNotes',
                                         ann_id='T{}'.format(T_id),
                                         note=word_dict[match.group().lower()][1])
                    new_doc.anns['notes'].append(new_note)
                    N_id += 1
                new_doc.anns['entities'].append(new_ent)
                T_id += 1
        # Update current span
        if sent == '\n':
            s_id += len(sent)
        else:
            s_id += len(sent) + 1

    print('Total sugggestions: {}'.format(total_sugs))
    return new_doc


def clean_overlapping_suggestions(doc):
    """
    Clean created suggestions that overlap with other entities in the document
    """
    # Create a new document
    new_doc = ann_structure.AnnSentence()
    new_doc.name = doc.name
    # Retrieve suggestions and existing annotations separately
    suggs = [ann for ann in doc.anns['entities'] if ann.tag.startswith('_SUG_')]
    existing_anns = [ann for ann in doc.anns['entities'] if not ann.tag.startswith('_SUG_')]

    # Compare each suggestion with the existing annotations.
    # If our suggestion has the exact same span or is inside another annotation, delete it.
    for sugg in suggs:
        if any([sugg.compare_overlap(ann) not in ['exact', 'nested-smaller'] for ann in existing_anns]):
            pass
            # TODO: Finish function


def generate_suggestions_from_tsv(corpus, tsv, outpath):
    """
    Creates suggestions for a whole corpus using suggestions from a TSV file.
    The TSV file must have three columns (with headers): span, label and code
    """
    word_dict = {}
    with open(tsv, 'r') as f_in:
        reader = csv.DictReader(f_in, delimiter='\t')
        for line in reader:
            word_dict[line['span']] = (line['label'], line['code'])
    for doc in corpus.docs:
        new_doc = generate_suggestion_re(doc, word_dict)
        rwsl.write_ann_file(new_doc, outpath)


def generate_tsv_for_suggestions(corpus, outpath):
    pass


if __name__ == '__main__':
    pass