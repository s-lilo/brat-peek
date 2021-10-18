'''
Visualization and stats reporting.
'''

import csv
from collections import defaultdict
import os

import seaborn as sns
from pandas import DataFrame as df
import matplotlib.pyplot as plt

sns.set_theme(style="darkgrid")


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
def generate_corpus_stats_tsv(ann_corpus, include_txt=False):
    '''
    Generates a .tsv file with an overview of the corpus.
    Includes: number of documents, total and average of sentences and tokens (if include_txt is set to True),
              total and average of entities both in general and by text label.
    :param ann_corpus: AnnCorpus object
    :param include_txt: whether to calculate text statistics or not. If set to true, the AnnCorpus object must
                        have been created using the txt parameter.
    # TODO: Allow to calculate statistics by collections in corpus.
    # TODO: Tokenization is very, very naïve. Use actual tokenizers.
    '''
    out_path = os.path.join('/'.join(ann_corpus.path.split('/')[:-1]), '{}_corpus_summary.tsv'.format(ann_corpus.name))
    with open(out_path, 'w') as f_out:
        writer = csv.writer(f_out, delimiter='\t')
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
        writer.writerow(first_row)

        # Create accumulator to count entities
        accum = defaultdict(list)
        # Get statistics for each document
        for doc in ann_corpus.docs:
            if include_txt:
                # TODO: Use actual tokenizer
                accum['sents'].append(sum([sent.count('.') for sent in doc.txt]))
                accum['tokens'].append(sum([len(sent.split(' ')) for sent in doc.txt]))
            for label in ann_corpus.text_labels:
                accum[label].append(doc.count['entities'][label] if doc.count['entities'][label] else 0)
            accum['entities'].append(len(doc.anns['entities']))

        # Create statistics row
        stats_row = [ann_corpus.name, len(ann_corpus.docs)]
        # Get total and average of sentences and tokens
        if include_txt:
            stats_row.extend([sum(accum['sents']), round(sum(accum['sents']) / len(accum['sents']), 2),
                              sum(accum['tokens']), round(sum(accum['tokens']) / len(accum['tokens']), 2)])
        # Get total numbers for labels
        stats_row.append(sum(accum['entities']))
        for label in ann_corpus.text_labels:
            stats_row.append(sum(accum[label]))
        # Get average numbers for labels
        stats_row.append(round(sum(accum['entities']) / len(accum['entities']), 2))
        for label in ann_corpus.text_labels:
            stats_row.append(round(sum(accum[label]) / len(accum[label]), 2))

        writer.writerow(stats_row)
        print('Written .tsv stats file to {}'.format(out_path))


if __name__ == '__main__':
    pass
