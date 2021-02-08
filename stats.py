'''
Visualization and stats reporting.
'''
import ann_structure

from datetime import datetime

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


# Report
# def generate_report_corpus(ann_corpus):
#     """
#     Generates corpus level statistics report. Set verbose to True for more detailed info.
#     :param ann_corpus: AnnDocument
#     :return: string
#     """
#     # Setting up
#     report = ""
#     separator = "###############################################\n"
#
#     # Header
#     header = "Annotation Report for file {}\n".format(ann_corpus.name)
#     header += datetime.now().strftime("%I:%M%p, %B %d %Y\n")
#
#     # Body
#     body = ""
#     body += "General statistics\n"
#
#     for k in ann_corpus.count.keys():
#         body += ""
#     # Put everything together
#     report += separator + header + separator + body + separator


if __name__ == '__main__':
    pass
