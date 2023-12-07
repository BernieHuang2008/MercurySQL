Introduction to MercurySQL Drivers
==================================

.. warning::
   All Drivers **MUST** be defined as subclasses of the `BaseDriver <base.html>`_ class.


Versioning
----------
**About Versioning**:

Every version name is composed of 3 numbers separated by dots (e.g. `1.0.0`).

- The first number is the **major** version. Major versions are incompatible.
- The second number is the **minor** version. Minor versions are **Backwards Compatible**. This means that the driver **MUST** be compatible with the previous minor version of MercurySQL, only adding some new features.
- The third number is the **patch** version. Patch versions are compatible.

**In short**, if the following conditions are met, the driver will be judged as `incompatible` with the current version of MercurySQL:

- `driver.major != mercury.major`
- `driver.minor < mercury.minor`

Drivers which are not compatible with the current version of MercurySQL will raise an `DriverIncompatibleError` exception.

