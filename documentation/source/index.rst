=======
Walk-ER
=======

.. image:: https://raw.githubusercontent.com/starling-lab/Walk-ER/master/media/WalkERLogo.png
   :align: center
   :alt: Walk-ER Logo, Automatic Construction of Background Knowledge

Convert entity-relationship diagrams to "modes" in order to constrain the search space in relational learning systems.

"Modes" are typically used in relational learning systems
(`Aleph <https://www.cs.ox.ac.uk/activities/programinduction/Aleph/aleph.html>`_,
`BoostSRL <https://starling.utdallas.edu/software/boostsrl>`_) to constrain the search space of hypotheses. However,
they are typically written using domain-specific languages designed by (and for) people who are already experts in
Inductive Logic Programming.

"Walk-ER" performs this same function using entity-relationship diagrams (ERDs).  ERDs are usually employed in the
design of relational databases, and should be familiar to many people who have worked with structured query language
(SQL) or relational database management systems (RDBMs).

Citing
------

If you find these ideas interesting or want to build on this line of work, please cite the following paper:

.. code-block:: tex

   @inproceedings{kcap2017ermodeconstruction,
     author = {Alexander Hayes and Mayukh Das and Phillip Odom and Sriraam Natarajan},
     title  = {User Friendly Automatic Construction of Background Knowledge: Mode Construction from ER Diagrams},
     booktitle = {KCAP},
     year   = {2017}
   }


Getting Started
---------------


Clone a copy of the repository from here_ and refer the :doc:`/user_guide/index`..




.. toctree::
  :hidden:
  :maxdepth: 3

  user_guide/index

.. _here: https://github.com/harshakokel/Walk-ER

