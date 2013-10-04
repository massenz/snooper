=========================
Snooper - Promotion Codes
=========================

:Date: 2013-10-03
:Author: M. Massenzio
:Version: 0.2
:Updated: 2013-10-03


Promotion Codes
+++++++++++++++

A special case is the use of the script to generate *promotion codes* as defined in the
specification_ in which case the arguments used are as follows::

    --coupons NUM           number of coupons to be generated
    --provider PROVIDER     name of the Service Provider for the coupons
    --cloud CLOUD           name of the Cloud Target for the coupons
    --out FILE              a file that will contain a promotion code per line (generated)

This can only be used with a configuration option that uses the credentials of a user that is
granted ``UPDATE`` priviliges to the ``PROMOTION_CODES`` table (see `Connection parameters`_).

.. _specification: https://github.com/RiverMeadow/encloud/blob/develop/docs/coupons.rst

An example invocation would be::

    python snooper.py --coupons=3 --provider=VMWare --cloud=vcloudTarget \
        --out=/Users/marco/coupons.txt --conf=snooper.conf --env=dev --host=10.10.121.99

Both the ``provider`` and the ``cloud`` **MUST** exist in the database for the coupons to be
successfully generated.

To get all service providers available, use::

    python snooper.py --conf snooper.conf --host 10.10.121.99 --env dev \
            "SELECT * FROM ORGANIZATIONS WHERE TYPE='SERVICE_PROVIDER'"

and similarly for cloud targets::

    python src/snooper.py --conf snooper.conf --host 10.10.121.99 --env dev \
            "SELECT name FROM CLOUD_TARGETS"

To get the cloud targets available only for a given service provider (whose ``name`` was retrieved
with the query above), use this query::

    "SELECT t.name FROM CLOUD_TARGETS t, ORGANIZATIONS o WHERE t.provider_ref = o.uuid \
            AND o.name='name' AND o.type='SERVICE_PROVIDER'"

Promotion Codes REST API
++++++++++++++++++++++++

They can be created using the following endpoint and parameters::

    POST /codes/<int:count>

    {
        "created_by": "1xa@rivermeadow.com",
        "cloud_type": "VCLOUD",
        "cloud": "vcloudTarget",
        "provider": "VMWare"
    }

This will return a CSV file with a list of CODES.
