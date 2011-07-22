Python Object Graphs
====================

``objgraph`` is a module that lets you visually explore Python object graphs.

You'll need `graphviz <http://www.graphviz.org/>`_ if you want to draw
the pretty graphs.

I recommend `xdot <http://pypi.python.org/pypi/xdot>`_ for interactive use.
``pip install xdot`` should suffice; objgraph will automatically look for it
in your ``PATH``.


Installation and Documentation
------------------------------

``pip install objgraph`` or `download it from PyPI
<http://pypi.python.org/pypi/objgraph>`_.

Documentation lives at http://mg.pov.lt/objgraph.


.. _history:

History
-------

I've developed a set of functions that eventually became objgraph when I
was hunting for memory leaks in a Python program.  The whole story -- with
illustrated examples -- is in this series of blog posts:

* `Hunting memory leaks in Python
  <http://mg.pov.lt/blog/hunting-python-memleaks.html>`_
* `Python object graphs
  <http://mg.pov.lt/blog/python-object-graphs.html>`_
* `Object graphs with graphviz
  <http://mg.pov.lt/blog/object-graphs-with-graphviz.html>`_


.. _devel:

Support and Development
-----------------------

The source code can be found in this Bazaar repository:
https://code.launchpad.net/~mgedmin/objgraph/trunk.

To check it out, use ``bzr branch lp:objgraph``.

Report bugs at https://bugs.launchpad.net/objgraph.

