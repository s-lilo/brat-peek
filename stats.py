'''
Visualization and stats reporting.
'''
import ann_structure

import csv
import os
import unidecode

import seaborn as sns
import matplotlib.pyplot as plt

from collections import defaultdict

from pandas import DataFrame as df

# import spacy

sns.set_theme(style="darkgrid")

# nlp = spacy.load("es_core_news_sm")

# Plot
def plot_tags(ann_corpus):
    '''

    :param ann_corpus:
    :return: nothing, just shows a plot.
    '''
    ent_df = df.from_dict(ann_corpus.count['entities'], orient='index').reset_index()
    ent_df = ent_df.rename(columns={'index': 'entity', 0: 'count'})
    sns.barplot(x=ent_df['entity'], y=ent_df['count'])
    plt.show()


# Overview
def generate_corpus_stats_tsv(ann_corpus, out_path, collections=False, include_txt=False):
    '''
    Generates a .tsv file with an overview of the corpus.
    Includes: number of documents, total and average of sentences and tokens (if include_txt is set to True),
              total and average of entities both in general and by text label.
    :param ann_corpus: AnnCorpus object
    :param out_path: string, path where the tsv will be written to
    :param collections: whether to calculate statistics for each collection in corpus individually.
    :param include_txt: whether to calculate text statistics or not. If set to true, the AnnCorpus object must
                        have been created using the txt parameter.
    # TODO: Tokenization is very, very naïve. Use actual tokenizers.
    '''
    with open(out_path + '/{}_corpus_summary.tsv'.format(ann_corpus.name), 'w') as f_out:
        # Creater header row
        first_row = ["corpus", "docs"]
        # Columns for text statistics
        if include_txt:
            first_row.extend(["total_sents", "avg_sents", "total_tokens", "avg_tokens"])
        # Columns for total number of entities
        first_row.append("total_entities")
        first_row.extend(['total_{}'.format(label) for label in ann_corpus.text_labels])
        # Columns for average number of entities
        first_row.append("avg_entities")
        first_row.extend(['avg_{}'.format(label) for label in ann_corpus.text_labels])
        # Write header
        writer = csv.DictWriter(f_out, fieldnames=first_row, delimiter='\t')
        writer.writeheader()
        # Create dict with all of the tsv's columns
        columns = {c: 0 for c in first_row}

        if collections:
            if not ann_corpus.collections:
                raise Exception('No collections found in AnnCorpus')
            corpus_coll = defaultdict(list)
            # Separate each collection's documents
            for coll in ann_corpus.collections:
                for doc in ann_corpus.docs:
                    if doc.collection == coll:
                        corpus_coll[coll].append(doc)
            # Get stats for each collection
            for k in corpus_coll.keys():
                # Create subcorpus
                subcorpus = ann_structure.AnnCorpus(path='', from_list=corpus_coll[k])
                subcorpus.name = k
                # Restart columns dict
                columns = {c: 0 for c in first_row}
                stats_row = create_stats_row(subcorpus, columns, include_txt=include_txt)
                writer.writerow(stats_row)
        else:
            stats_row = create_stats_row(ann_corpus, columns, include_txt=include_txt)
            writer.writerow(stats_row)

        print('Written .tsv stats file to {}'.format(out_path + '/{}_corpus_summary.tsv'.format(ann_corpus.name)))


def create_stats_row(ann_corpus, columns, include_txt=False):
    # Create accumulator to count entities
    accum = defaultdict(list)
    # Get statistics for each document
    for doc in ann_corpus.docs:
        if include_txt:
            # TODO: Not too reliable, use actual tokenizer
            accum['sents'].append(len([sent.split('.') for sent in doc.txt]))
            accum['tokens'].append(len([sent.split(' ') for sent in doc.txt]))
        for label in ann_corpus.text_labels:
            accum[label].append(doc.count['entities'][label] if doc.count['entities'][label] else 0)
        accum['entities'].append(len(doc.anns['entities']))

    # Fill in columns dictionary
    columns['corpus'] = ann_corpus.name
    columns['docs'] = len(ann_corpus.docs)
    # Get total and average of sentences and tokens
    if include_txt:
        columns['total_sents'] = sum(accum['sents'])
        columns['avg_sents'] = round(sum(accum['sents']) / len(accum['sents']), 2)
        columns['total_tokens'] = sum(accum['tokens'])
        columns['avg_tokens'] = round(sum(accum['tokens']) / len(accum['tokens']), 2)
    # Get total numbers for labels
    columns['total_entities'] = sum(accum['entities'])
    for label in ann_corpus.text_labels:
        columns['total_{}'.format(label)] = sum(accum[label])
    # Get average numbers for labels
    columns['avg_entities'] = round(sum(accum['entities']) / len(accum['entities']), 2)
    for label in ann_corpus.text_labels:
        columns['avg_{}'.format(label)] = round(sum(accum[label]) / len(accum[label]), 2)

    return columns


def print_corpus_summary(ann_corpus, verbose=False):
    """
    Describes a corpus using some general statistics
    """
    print('# SUMMARY FOR CORPUS {} AT {}'.format(ann_corpus.name, ann_corpus.path))
    print('This corpus has a total of {} documents.'.format(len(ann_corpus.docs)))
    print('This corpus has a total of {} text annotations from {} labels'.format(sum(ann_corpus.count['entities'].values()), len(ann_corpus.text_labels)))
    print('The labels in this corpus are: {}'.format(', '.join([label for label in ann_corpus.text_labels])))
    if verbose:
        print('\nThis is the label distribution in the corpus:')
        # TODO: Make it pretty
        for label in ann_corpus.text_labels:
            print('{} | Total: {} | Unique: {} ({}% of total), {} ({}% of total) lowercased'.
                  format(label,
                         ann_corpus.count['entities'][label],
                         len(ann_corpus.text_freq[label]),
                         round((len(ann_corpus.text_freq[label]) / ann_corpus.count['entities'][label]) * 100, 2),
                         len(ann_corpus.text_freq_lower[label]),
                         round((len(ann_corpus.text_freq_lower[label]) / ann_corpus.count['entities'][label]) * 100, 2)
                         ))
        print('TOTAL | Total: {} | Unique: {} ({}% of total), {} ({}% of total) lowercased'.format(
            sum(ann_corpus.count['entities'].values()),
            sum([len(ann_corpus.text_freq[lab].values()) for lab in ann_corpus.text_labels]),
            round(sum([len(ann_corpus.text_freq[lab].values()) for lab in ann_corpus.text_labels]) / sum(ann_corpus.count['entities'].values()) * 100, 2),
            sum([len(ann_corpus.text_freq_lower[lab].values()) for lab in ann_corpus.text_labels]),
            round(sum([len(ann_corpus.text_freq_lower[lab].values()) for lab in ann_corpus.text_labels]) / sum(ann_corpus.count['entities'].values()) * 100, 2)))
        print('\nThis is the top 10 most common (lowercased) annotations for each tag:')
        for label in ann_corpus.text_labels:
            print('- {} | {}'.
                  format(label, ann_corpus.text_freq_lower[label].most_common(10)
                         ))

if __name__ == '__main__':
    pass