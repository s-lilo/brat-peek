# BRAT Peek 👀

Peek into corpora annotated using brat rapid annotation tool ([brat][brat]).

[brat]: http://brat.nlplab.org/index.html

## Features
* Framework for working with .ann files and collections.
        
        import peek
        corpus = peek.AnnCorpus('dummy_data/')
        # Access a random document...
        doc = corpus.get_random_doc()
        # ...or get one by its name
        doc = corpus.get_doc_by_name('PMID-1590827')
        # Or maybe just get those you're interested in
        docs = [doc for doc in corpus.docs if 'Organism' in doc.count['entities']]
        # Print document name and path
        print(doc.name, doc.path)
        # See the individual annotations in a document
        print(doc.anns.items())

* See the annotations in a corpus at a glance with stats and graphs.
    
        print('Corpus stats:', corpus.count)
        print('Entity labels found in corpus: ', corpus.text_labels)
        print('Document 42:', corpus.docs[42])
        # Create a plot
        peek.stats.plot_tags(corpus)
  
* Check out the most common annotated text spans.
  
        print(corpus.text_freq)
        print(corpus.text_freq['Organism'].most_common(5))

* Print a corpus's content to a .tsv file.
  
        # Create .tsv file from corpus (to_ignore is an optional argument)
        peek.rwsl.print_tsv_from_corpus(corpus, 'output_folder/', to_ignore=['Organism'])
        # Create .tsv with text frequencies
        peek.rwsl.print_tsv_from_text_freq(corpus, 'output_folder/', to_ignore=['Organism'])
        # Create .tsv with codes column for normalization with a code reference file.
        peek.rwsl.print_tsv_for_norm(corpus, 'output_folder/', 'reference.tsv', to_ignore=['Organism'])

* Calculate IAA of different corpora.
  
        # Calculate IAA and print .tsv file with disagreements
        corpus2 = AnnCorpus('dummy_data2/')
        peek.metrics.show_iaa([corpus, corpus2], ['filename', 'label', 'offset'], ['Organism'], tsv=True)
        # Get IAA for all categories in the corpus
        peek.metrics.show_iaa([corpus, corpus2], ['filename', 'label', 'offset'], corpus.text_labels)

* Extract sentences from documents to create customizable annotation files.
        
        # Set txt to True when creating an AnnCorpus object to also read .txt files
        corpus = peek.AnnCorpus('dummy_data/', txt=True)
        # Separate document into individual sentences, adjusting annotation spans in the way.
        sentences = [peek.txt.doc2sent(doc) for doc in corpus.docs]
        # Create a new document only with sentences that have organisms annotated.
        new_doc = peek.txt.sent2doc([sent for sent in sentences if any(ann.tag == 'Organism' for ann in frase_med.anns['entities'])])

* Save corpora as pickle objects to load them later (useful for big corpora).

        # Save
        peek.rwsl.save_corpus(corpus, 'temp/')
        # Load
        corpus = peek.rwsl.load_corpus('temp/dummy_data.pckl')