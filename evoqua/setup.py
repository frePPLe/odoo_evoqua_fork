#
# This code was developed by frePPLe bv for Evoqua.
#
# Evoqua has full copyright and intellectual property rights.
# FrePPLe reserves the rights to apply the techniques and
# reuse the code for other implementations.
#

import setuptools

setuptools.setup(
    name="evoqua",
    description="frePPLe extension module for Evoqua",
    author="frepple.com",
    author_email="jdetaeye@frepple.com",
    version="1.0",
    packages=["evoqua", ],
    package_dir={"evoqua": "."},
    package_data={
        "": ["templates/**/*"],
    },
    include_package_data=True,
    zip_safe=False,
)
