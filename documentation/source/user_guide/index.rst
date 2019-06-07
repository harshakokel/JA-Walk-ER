==========
User Guide
==========


Walk-ER can either be invoked from a terminal or invoked from a graphical user interface. To get started, clone_ the Walk-ER code from github.


GUI version
-----------

Walk-ER GUI allows user to create a simple ER diagram consisting of entities, attributes, and relations (square, ellipse and diamond shape respectively) and provides mode representation. Walk-ER GUI is built on top of Doteditor_.

    The dependency list includes:

    1. Graphviz >= 2.66
    #. wxpython >= 3.0
    #. PLY == 3.4
    #. colour >= 0.1.1

    Refer to the Doteditor github_ page for issues in dependencies.

Run the Walk-ER GUI, using following command:

>>> python /src/walkergui.py

This should pop up the Walk-ER GUI. You can now create the ER model for your data set. The GIF below displays how to add nodes & edges to create a simple ER diagram and view the modes. Target variables are to be highlighted in blue and important variables are highlighted in red. **It is necessary to have a target variable to view the modes.**


.. image:: ../images/webkb.gif


Some additional capabilities of Walk-ER GUI are:

1. Allows to save the ER diagram as ``.dot`` file
#. Lets you export modes to a text file
#. Lets you import the ``.dot`` file

Walker-GUI currently only supports exhaustive walk to find the modes. For other walks, you can export the ``.dot`` file and use the interactive version.



Interactive version
-------------------

Interactive version of Walker support input of ER-diagram in two formats: ``.dot`` and a custom ``.mayukh`` files.


>>> python walker.py -h
usage: walker.py [-h] [-v] [--number NUMBER] [-w | -s | -n | -e | -r | -rw]
                 [-d]
                 diagram_file
Walk-ER: a system for walking the paths in an entity-relational diagram.
Written by Alexander L. Hayes (Alexander.Hayes@utdallas.edu)) and Mayukh Das.
University of Texas at Dallas. STARAI Lab (dir. Professor Natarajan).
positional arguments:
  diagram_file
optional arguments:
  -h, --help         show this help message and exit
  -v, --verbose      Increase verbosity to help with debugging.
  --number NUMBER    Select number of features to walk to (assumes that
                     Important features are ordered from most important to
                     least important). Defaults to number_attributes +
                     number_relations if chosen number is greater than both.
  -w, --walk         [Default] Walk graph from target to features.
  -s, --shortest     Walk the graph from target to features. If there are
                     multiple paths, take the shortest. If the shortest are
                     equal lengths, walk both.
  -n, --nowalk       [Not implemented] Instantiate variables without walking.
  -e, --exhaustive   Walk graph from every feature to every feature.
  -r, --random       Ignore features the user selected and walk (-w) from the
                     target to random features.
  -rw, --randomwalk  Walk a random path from the target until reaching a depth
                     limit (specified with --number).
  -d, --dot          Graph provided in dot format.
Copyright 2017 Free Software Foundation, Inc. License GPLv3+: GNU GPL version
3 or later <http://gnu.org/licenses/gpl.html>. This is free software: you are
free to change and redistribute it. There is NO WARRANTY, to the extent
permitted by law.



Examples:

* >>> python src/walker.py -w diagrams/imdb.mayukh

* >>> python src/walker.py -w -d dots/imdb.dot

* >>> python src/walker.py -rw --number 10 diagrams/imdb.mayukh

* >>> python src/walker.py -s -d dots/imdb.dot



.. _Doteditor: http://vincenthee.github.io/DotEditor/
.. _github: https://github.com/vincenthEE/DotEditor
.. _clone: https://github.com/harshakokel/Walk-ER

