from ann_structure import *
import stats
import rwsl
import iaa

if __name__ == "__main__":
    dummy = AnnCorpus('dummy_data/')
    corpus2 = AnnCorpus('dummy_data2/')
    iaa.show_iaa([dummy, corpus2], ['filename', 'label', 'offset'], ['Organism'], tsv=True)
