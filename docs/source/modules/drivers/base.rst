**[Driver]**: Base
==================

.. warning::
   All Drivers **MUST** be defined as subclasses of this `BaseDriver` class.

Version & Informations
----------------------
.. autoattribute:: MercurySQL.drivers.base.BaseDriver.version

Dependencies
------------
- `None`

Subclasses / Methods
--------------------

.. autoattribute:: MercurySQL.drivers.base.BaseDriver.payload

.. autoclass:: MercurySQL.drivers.base.BaseDriver.Conn
   :members:
   :undoc-members:
   :special-members:
   :exclude-members: __weakref__, __module__, __dict__

.. autoclass:: MercurySQL.drivers.base.BaseDriver.Cursor
   :members:
   :undoc-members:
   :special-members:
   :exclude-members: __weakref__, __module__, __dict__

.. autoclass:: MercurySQL.drivers.base.BaseDriver.APIs
   :members:
   :undoc-members:
   :special-members:
   :exclude-members: __weakref__, __module__, __dict__

.. autoclass:: MercurySQL.drivers.base.BaseDriver.TypeParser
   :members:
   :undoc-members:
   :special-members:
   :exclude-members: __weakref__, __module__, __dict__
