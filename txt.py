"""
Read corpus text for different purposes.
"""
import ann_structure

from nltk.tokenize import sent_tokenize


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
        ann_sent.txt = sent
        # Get sentence spans
        if sent != '\n':
            ending_span = current_span + len(sent)
        else:
            # Brat doesn't count newlines. If we add them to our ending span, we'll be off by one ch for every newline.
            ending_span = current_span
        # Get annotations for the sentence
        for ent in doc.anns['entities']:
            # If the annotation's span is inside the sentence's, construct a new AnnSentence
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
        ann_sent.txt += sent.txt + '\n'
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


if __name__ == "__main__":
    import rwsl
    prueba = ann_structure.AnnCorpus('/home/salva/Documents/corpora/clinic/informes_alta_primer_analisis/corrected', txt=True)

    prueba.create_collections(['negation', 'meddocan'])
    negation_sents = []
    negation = [doc for doc in prueba.docs if doc.collection == 'negation']
    meddocan = [doc for doc in prueba.docs if doc.collection == 'meddocan']
    for doc_neg, doc_med in zip(negation, meddocan):
        frases_neg = doc2sent(doc_neg)
        frases_med = doc2sent(doc_med)
        for frase_neg, frase_med in zip(frases_neg, frases_med):
            if any([ann.tag == 'TERRITORIO' for ann in frase_med.anns['entities']]) and \
                    any([ann.tag == 'NEG' for ann in frase_neg.anns['entities']]):
                negation_sents.append(frase_neg)
                print('FRASE:', frase_neg, frase_neg.txt)
                # rwsl.write_ann_file(frase, output_path='dummy_data3')
                # rwsl.write_txt_file(frase, output_path='dummy_data3')
    new_doc = sent2doc(negation_sents)
    rwsl.write_ann_file(new_doc, output_path='dummy_data3')
    rwsl.write_txt_file(new_doc, output_path='dummy_data3')