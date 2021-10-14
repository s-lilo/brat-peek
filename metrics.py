"""
Calculate different metrics by comparing two or more corpora.

Adaptation of Antonio Miranda's IAA computation script (https://github.com/TeMU-BSC/iaa-computation) and MEDDOPROF's
evaluation library for precision, recall, F-1 measure (https://github.com/TeMU-BSC/meddoprof-evaluation-library)
"""
from collections import Counter

import os
import pandas as pd
import numpy as np
import warnings


def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
    return '%s:%s: %s: %s\n' % (filename, lineno, category.__name__, message)


warnings.formatwarning = warning_on_one_line


# Show metrics
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

    EXAMPLE USE:
    peek.metrics.show_iaa([corpus1, corpus2], ['filename', 'label', 'offset'], ['label1', ...])
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


def show_fscore(gs, pred, rel_labels):
    """
    Compute F-score by comparing a GS brat-annotated corpus and a set of predictions also in brat format.
    :param gs: Gold Standard as AnnCorpus object.
    :param pred: Predictions as AnnCorpus object.
    :param rel_labels: list of labels to consider for F-score.
    # TODO: Print tsv
    """

    ##### GET ANN INFORMATION #####

    doc_list_gs = [doc.name for doc in gs.docs]

    info_gs = []
    for doc in gs.docs:
        for ann in doc.anns['entities']:
            if ann.tag in rel_labels:
                span = " ". join([str(n) for tup in ann.span for n in tup])
                info_gs.append([gs.name, doc.name, ann.name, ann.tag, ann.text, span])
    gs = pd.DataFrame(info_gs, columns=['annotator', 'filename', 'mark',
                                        'label', 'offset', 'span'])

    info_pred = []
    for doc in pred.docs:
        for ann in doc.anns['entities']:
            # TODO: CODES
            if ann.tag in rel_labels:
                span = " ". join([str(n) for tup in ann.span for n in tup])
                info_pred.append([pred.name, doc.name, ann.name, ann.tag, ann.text, span])
    pred = pd.DataFrame(info_pred, columns=['annotator', 'filename', 'mark',
                                            'label', 'offset', 'span'])

    if pred.shape[0] == 0:
        raise Exception('There are not parsed predicted annotations')
    elif gs.shape[0] == 0:
        raise Exception('There are not parsed Gold Standard annotations')

    # Drop duplicates
    pred = pred.drop_duplicates(['filename', 'label', 'offset']).copy()
    gs = gs.drop_duplicates(['filename', 'label', 'offset']).copy()

    relevant_columns = ["filename", "offset", "label"]

    # Predicted Positives:
    Pred_Pos_per_cc = \
        pred.drop_duplicates(subset=relevant_columns). \
            groupby("filename")["offset"].count()
    Pred_Pos = pred.drop_duplicates(subset=relevant_columns).shape[0]

    # Gold Standard Positives:
    GS_Pos_per_cc = \
        gs.drop_duplicates(subset=relevant_columns). \
            groupby("filename")["offset"].count()
    GS_Pos = gs.drop_duplicates(subset=relevant_columns).shape[0]

    # Eliminate predictions not in GS (prediction needs to be in same clinical
    # case and to have the exact same offset to be considered valid!!!!)
    df_sel = pd.merge(pred, gs,
                      how="right",
                      on=relevant_columns)
    is_valid = df_sel.apply(lambda x: x.isnull().any() == False, axis=1)
    df_sel = df_sel.assign(is_valid=is_valid.values)

    # True Positives:
    TP_per_cc = (df_sel[df_sel["is_valid"] == True]
                 .groupby("filename")["is_valid"].count())
    TP = df_sel[df_sel["is_valid"] == True].shape[0]

    # Add entries for clinical cases that are not in predictions but are present
    # in the GS
    cc_not_predicted = (pred.drop_duplicates(subset=["filename"])
                        .merge(gs.drop_duplicates(subset=["filename"]),
                               on='filename',
                               how='right', indicator=True)
                        .query('_merge == "right_only"')
                        .drop('_merge', 1))['filename'].to_list()
    for cc in cc_not_predicted:
        TP_per_cc[cc] = 0

    # Add TP = 0 in clinical cases where all predictions are wrong
    for doc in doc_list_gs:
        if doc not in TP_per_cc.index.tolist():
            TP_per_cc[doc] = 0

    # Remove entries for clinical cases that are not in GS but are present
    # in the predictions
    cc_not_GS = (gs.drop_duplicates(subset=["filename"])
                 .merge(pred.drop_duplicates(subset=["filename"]),
                        on='filename',
                        how='right', indicator=True)
                 .query('_merge == "right_only"')
                 .drop('_merge', 1))['filename'].to_list()
    Pred_Pos_per_cc = Pred_Pos_per_cc.drop(cc_not_GS)

    # Calculate Final Metrics:
    P_per_cc = TP_per_cc / Pred_Pos_per_cc
    P = TP / Pred_Pos
    R_per_cc = TP_per_cc / GS_Pos_per_cc
    R = TP / GS_Pos
    F1_per_cc = (2 * P_per_cc * R_per_cc) / (P_per_cc + R_per_cc)
    if (P + R) == 0:
        F1 = 0
        warnings.warn('Global F1 score automatically set to zero to avoid division by zero')
        return P_per_cc, P, R_per_cc, R, F1_per_cc, F1
    F1 = (2 * P * R) / (P + R)

    if (any([F1, P, R]) > 1) | any(F1_per_cc > 1) | any(P_per_cc > 1) | any(R_per_cc > 1):
        warnings.warn(
            'Metric greater than 1! You have encountered an undetected bug, please, contact antoniomiresc@gmail.com!')

    # return P_per_cc, P, R_per_cc, R, F1_per_cc, F1
    ###### Show results ######
    print('\n-----------------------------------------------------')
    print('Clinical case name\t\t\tPrecision')
    print('-----------------------------------------------------')
    for index, val in P_per_cc.items():
        print(str(index) + '\t\t' + str(round(val, 3)))
        print('-----------------------------------------------------')

    print('\n-----------------------------------------------------')
    print('Clinical case name\t\t\tRecall')
    print('-----------------------------------------------------')
    for index, val in R_per_cc.items():
        print(str(index) + '\t\t' + str(round(val, 3)))
        print('-----------------------------------------------------')

    print('\n-----------------------------------------------------')
    print('Clinical case name\t\t\tF-score')
    print('-----------------------------------------------------')
    for index, val in F1_per_cc.items():
        print(str(index) + '\t\t' + str(round(val, 3)))
        print('-----------------------------------------------------')

    print('\n_____________________________________________________')
    print('Micro-average metrics')
    print('_____________________________________________________')
    print('\nMicro-average precision = {}\n'.format(round(P, 3)))
    print('\nMicro-average recall = {}\n'.format(round(R, 3)))
    print('\nMicro-average F-score = {}\n'.format(round(F1, 3)))


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
