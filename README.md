# BRAT Peek 👀

Peek into corpora annotated using brat rapid annotation tool ([brat][brat]).

[brat]: http://brat.nlplab.org/index.html

## Features
* Framework for working with .ann files and collections.
* See the annotations in a corpus at a glance with stats and graphs.
* Check out the most common annotated text spans.
* Print a corpus's content to a .tsv file.
* Calculate IAA of different corpora.

## Example Use
    import peek
    # Open a corpus
    corpus = peek.AnnCorpus('dummy_data/')
    print('Corpus stats:', corpus.count)
    print('Document 42:', corpus.docs[42])
    print('Document 42 stats:', corpus.docs[42].count)
    # Access a random document
    doc = corpus.get_random_doc()
    # Print document name and path
    print(doc.name, doc.path)
    # Print entities in document
    print(doc.anns['entities'])
    # Counter with text annotations
    print(corpus.text_freq)
    print(corpus.text_freq['Organism'].most_common(5))
    # Create a plot
    peek.stats.plot_tags(corpus)
    # Create tsv file from corpus
    peek.rwsl.print_tsv_from_corpus(corpus, '.', to_ignore=['Organism'])
    # Calculate IAA and print .tsv file with disagreements
    corpus2 = AnnCorpus('dummy_data2/')
    peek.iaa.show_iaa([corpus, corpus2], ['filename', 'label', 'offset'], ['Organism'], tsv=True)