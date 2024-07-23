MercurySQL.errors
=================

Here are the exceptions that may be raised by MercurySQL.

Basic Errors
------------

There are many type of errors that can be raised by MercurySQL.

However, all these errors are divided into a few main categories.
We have created some Basic Errors that are parent classes of all other errors.
So you can catch a whole category of errors by using the parent class.

.. autoclass:: MercurySQL.errors.MercurySQLError

.. autoclass:: MercurySQL.errors.MSQLSyntaxError

.. autoclass:: MercurySQL.errors.MSQLDriverError

Syntax Errors
-------------

Syntax Errors are often caused by misusing of MercurySQL's functions and syntax.

.. autoclass:: MercurySQL.errors.DuplicateError

.. autoclass:: MercurySQL.errors.NotExistsError

.. autoclass:: MercurySQL.errors.NotSupportedError

.. autoclass:: MercurySQL.errors.ConfilictError

.. autoclass:: MercurySQL.errors.NotSpecifiedError

.. _DRVERR:

Driver Errors
-------------------------

Driver Errors are all related to drivers.

A driver can raise these error for not working properly, and MSQL can also raise these errors when it detects something wrong that is related to driver.

.. autoclass:: MercurySQL.errors.DriverIncompatibleError
