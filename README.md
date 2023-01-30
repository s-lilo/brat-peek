# brat Peek 👀

> Peek into corpora annotated using brat rapid annotation tool ([brat][brat]).

**brat Peek** 👀 is a Python framework for working with annotations in brat's standoff format (`.ann` files).


[brat]: http://brat.nlplab.org/index.html

## Main features
- Load `.ann` files using an object-oriented framework that allows easy access and manipulation to complete corpora as well as to individual documents and annotations.
- Load `.txt` files to see annotations in context, check annotation spans and extract individual sentences.
- Print different annotation statistics and output corpus contents in multiple formats.
- Calculate evaluation metrics such as inter-annotator agreement and F-1 score between document collections.

## How to use brat peek 👀
A full documentation and example notebooks are in the works. Meanwhile, take a look at some examples of how to use brat peek 👀:

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
        print('Document 42 annotations:', corpus.docs[41].anns)
        # Create a plot
        peek.stats.plot_tags(corpus)
        # Generate .tsv with statistics
        peek.stats.generate_corpus_stats_tsv(corpus, include_txt=True)
  
* Check out the most common annotated text spans.
  
        print(corpus.text_freq)
        print(corpus.text_freq['Organism'].most_common(5))
        print(corpus.text_freq_lower)

* Print a corpus's content to a .tsv file.
  
        # Create .tsv file from corpus (to_ignore is an optional argument)
        peek.rwsl.print_tsv_from_corpus(corpus, 'output_folder/', to_ignore=['Organism'])
        # Create .tsv with text frequencies
        peek.rwsl.print_tsv_from_text_freq(corpus, 'output_folder/', to_ignore=['Organism'], lower=False)
        # Create .tsv with codes column for normalization with a code reference file.
        peek.rwsl.print_tsv_for_norm(corpus, 'output_folder/', 'reference.tsv', to_ignore=['Organism'])

* Calculate metrics for different corpora.
  
        # Calculate IAA and print .tsv file with disagreements [code based on https://github.com/TeMU-BSC/iaa-computation]
        peek.metrics.show_iaa([corpus1, corpus2], ['filename', 'label', 'offset'], ['Organism'], tsv=True)
        # You can use specific labels, as shown above, or use the text_labels attribute to use all the labels in the corpus at once.
        peek.metrics.show_iaa([corpus1, corpus2], ['filename', 'label', 'offset'], corpus1.text_labels)
        # Calculate precision, recall and F-score between a Gold Standard and a set of predictions [code based on https://github.com/TeMU-BSC/meddoprof-evaluation-library/]
        peek.metrics.show_fscore(gs, pred, gs.text_labels)

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

* Suggest annotations to speed up your annotation process (on the works - mostly untested)
      
        peek.txt.generate_suggestions_from_tsv(temp, tsv)


## Contact
brat peek is a personal project, which means that currently new features are added as I personally need them. 
If you have any questions or suggestions, you can contact me at the following address:
* Salvador Lima: <salvador.limalopez gmail com>

For more information on brat, please visit its [GitHub repository](https://github.com/nlplab/brat) or [homepage](http://brat.nlplab.org/).