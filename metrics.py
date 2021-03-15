"""
Calculate inter-annotator agreement (IAA) of two corpora.

Adaptation of Antonio Miranda's IAA computation script (https://github.com/TeMU-BSC/iaa-computation).
TODO: INCLUDE PRECISION, RECALL, F-score
"""
from collections import Counter

import os
import pandas as pd


# This is the main IAA function
def show_iaa(corpus_list, rel_variables, rel_labels, tsv=False):
    """
    Compute IAA from several annotators (all vs all and detailed) and for different labels (all together and per label).
    :param corpus_list: list of AnnCorpus.
    :param rel_variables: list with relevant variables in IAA computation.
        Possible values are: annotator, filename, mark, label, offset, span, code.
        If we choose "filename,label,offset", matches are annotations in the same file, with same label and in the same
        position in text. It is recommended to always use those three (filename,label,offset).
    :param rel_labels: list of labels to consider when computing IAA.
    :param tsv: Whether to output a tsv file with disagreement info.  # TODO: include IAA info in tsv?
    """
    annotator_names = [corpus.name for corpus in corpus_list]

    ##### GET ANN INFORMATION #####
    list_df = []
    for corpus in corpus_list:
        info = []
        for doc in corpus.docs:
            for ann in doc.anns['entities']:
                # TODO: CODES
                if ann.tag in rel_labels:
                    span = " ". join([str(n) for tup in ann.span for n in tup])
                    info.append([corpus.name, doc.name, ann.name, ann.tag, ann.text, span])
        df = pd.DataFrame(info, columns=['annotator', 'filename', 'mark',
                                         'label', 'offset', 'span'])
        list_df.append(df)

    if tsv:
        paths = list(map(lambda x: os.path.join('temp', x + '.tsv'), annotator_names))
        output_annotation_tables(list_df, paths)

        df1 = pd.read_csv(paths[0], sep='\t', header=0)
        df1 = df1.drop(['mark'], axis=1)

        df2 = pd.read_csv(paths[1], sep='\t', header=0)
        df2 = df2.drop(['mark'], axis=1)

        aux = pd.merge(df1, df2, how='outer', on=['filename', 'label', 'offset', 'span'])
        aux[aux.isnull().any(axis=1)].sort_values(by=['filename', 'span']). \
            to_csv('temp/disagreement.tsv', sep='\t', header=True, index=False)

    ##### COMPUTE IAA #####
    (iaa_all_vs_all, iaa_pairwise,
     iaa_by_label, count_labels) = computations(list_df, rel_variables,
                                                annotator_names, by_label=True)
    ###### PRINT ######
    print('_________________________________________________________________')
    print('\nIAA taking into account {}'.format(rel_variables))
    print('_________________________________________________________________')
    print('\n\n')
    print('-----------------------------------------------------------------')
    print('1. IAA all vs all')
    print('-----------------------------------------------------------------')
    print(round(iaa_all_vs_all, 3))
    print('\n\n')
    print('-----------------------------------------------------------------')
    print('IAA different annotators:')
    print('-----------------------------------------------------------------')
    print_iaa_annotators(annotator_names, iaa_pairwise)
    print('\n\n')
    print('-----------------------------------------------------------------')
    print('IAA per label:')
    print('-----------------------------------------------------------------')
    for k, v in sorted(iaa_by_label.items()):
        print(k + ': ' + str(round(v[0], 3)) + '\t(' + str(count_labels[k]) + ')')
    print('\n')


# These are all helper functions
def output_annotation_tables(list_df, outpaths):
    '''
    DESCRIPTION: output pandas DataFrames with annotations to TSV file

    Parameters
    ----------
    list_df: list
        List with annotation Dataframes. One Dataframe per annotator
    outpaths: list
        List with output paths. One path per annotation

    Returns
    -------

    '''
    for df, path in zip(list_df, outpaths):
        df.to_csv(path, sep='\t', index=False)


def computations(list_df, relevant_colnames, annotator_names, by_label=False):
    '''
    Compute IAA

    Parameters
    ----------
    list_df : list
        Contains one pandas dataframe per annotator.
    relevant_colnames : list
        List of relevant column names to compute IAA.
    by_label: boolean
        Whether to do the comparison label by label

    Returns
    -------
    iaa_all_vs_all: float
        IAA (pairwise agreement: intersection / union)
    iaa_pairwise: dict
        Contains IAA annotator by annotator
        Keys: annotators compared
        Values; float IAA (pairwise agreement: intersection / union)
    iaa_by_label: dict
        Contains IAA by label.
        Keys: label
        Values: tuple (iaa_all_vs_all, iaa_pairwise)
    '''
    # Get labels
    labels = []
    for df in list_df:
        labels = labels + df.label.to_list()
    count_labels = Counter(labels)
    labels = set(count_labels.keys())

    # Extract info from dataframe
    codes, _ = get_codes(list_df, relevant_colnames, labels)

    # Compute IAA
    iaa_all_vs_all, iaa_pairwise = compute_iaa(codes, annotator_names)

    if by_label == False:
        return iaa_all_vs_all, iaa_pairwise

    # In case we want to compute IAA per each label
    iaa_by_label = {}
    for label in labels:
        # Extract info from dataframe
        codes, _ = get_codes(list_df, relevant_colnames, [label])
        # Compute IAA
        iaa_all_vs_all_l, iaa_pairwise_l = compute_iaa(codes, annotator_names)

        iaa_by_label[label] = (iaa_all_vs_all_l, iaa_pairwise_l)
    return iaa_all_vs_all, iaa_pairwise, iaa_by_label, count_labels


def get_codes(list_df, relevant_colnames, rel_labels):
    '''
    Extract "codes" from dataframe.

    Parameters
    ----------
    list_df : list
        Contains one pandas dataframe per annotator.
    relevant_colnames : list
        List of relevant column names to compute IAA.
    rel_labels : list
        List of relevant values of the "label" column of dataframe.

    Returns
    -------
    codes : list
        Contains sets of codes for each dataframe.
    annotator_names : list
        Contains names of annotators.

    '''
    codes = []
    annotator_names = []
    for df in list_df:
        if df.shape[0] == 0:
            codes.append(set())
            annotator_names.append('empty')
            continue
        codes.append(set(df[relevant_colnames].
                         drop(df[df['label'].isin(rel_labels) == False].index).
                         drop_duplicates(subset=relevant_colnames).
                         agg('|'.join, axis=1).to_list()))
        annotator_names.append(df.annotator.drop_duplicates().to_list()[0])

    return codes, annotator_names


def compute_iaa(codes, annotator_names):
    '''
    Compute IAA given the codes and annotator names

    Parameters
    ----------
    codes : list
        Contains sets of codes for each dataframe.
    annotator_names : list
        Contains names of annotators.

    Returns
    -------
    iaa_all_vs_all: float
        IAA (pairwise agreement: intersection / union)
    iaa_pairwise: dict
        Contains IAA annotator by annotator
        Keys: annotators compared
        Values; float IAA (pairwise agreement: intersection / union)

    '''

    if len(set.union(*codes)) == 0:
        all_vs_all = 0
    else:
        all_vs_all = len(set.intersection(*codes)) / len(set.union(*codes))

    pairwise = {}
    for annotator1, annotations1 in zip(annotator_names, codes):
        for annotator2, annotations2 in zip(annotator_names, codes):
            comparison = (annotator1, annotator2)
            if len(annotations1.union(annotations2)) == 0:
                pairwise[comparison] = 0
                continue
            pairwise[comparison] = (len(annotations1.intersection(annotations2)) /
                                    len(annotations1.union(annotations2)))

    return all_vs_all, pairwise


def print_iaa_annotators(annotator_names, iaa_pairwise):
    '''
    Print IAA pairwise in a pretty way
    '''
    # Make sure iaa_pairwise and annotator_names have same order
    first_key = [k[0] for k, v in iaa_pairwise.items()]
    if first_key != sorted(first_key):
        print('Cannot display pretty pairwise information due to unknown ' +
              'sorting error. We proceed to display it in non-pretty way')
        print(iaa_pairwise)
        return
    # Print
    c = 0
    print(*([''] + annotator_names), sep='\t', end='')
    first_ann_old = ''
    for k, v in iaa_pairwise.items():
        first_ann = k[0]
        if first_ann != first_ann_old:
            print('\n')
            print(first_ann, end='')
            first_ann_old = first_ann
            c = 0
        c = c + 1
        print('\t', end='')
        print(str(round(v, 3)), end='')
