.. bitstruct documentation master file, created by
   sphinx-quickstart on Sat Apr 25 11:54:09 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. toctree::
   :maxdepth: 2

bitstruct - Interpret strings as packed binary data
===================================================

.. include:: ../README.rst

Functions
=========

.. autofunction:: bitstruct.pack
.. autofunction:: bitstruct.unpack
.. autofunction:: bitstruct.pack_into
.. autofunction:: bitstruct.unpack_from
.. autofunction:: bitstruct.pack_dict
.. autofunction:: bitstruct.unpack_dict
.. autofunction:: bitstruct.pack_into_dict
.. autofunction:: bitstruct.unpack_from_dict
.. autofunction:: bitstruct.calcsize
.. autofunction:: bitstruct.byteswap
.. autofunction:: bitstruct.compile

Classes
=======

.. autoclass:: bitstruct.CompiledFormat

   .. automethod:: pack
   .. automethod:: unpack
   .. automethod:: pack_into
   .. automethod:: unpack_from
   .. automethod:: pack_dict
   .. automethod:: unpack_dict
   .. automethod:: pack_into_dict
   .. automethod:: unpack_from_dict
