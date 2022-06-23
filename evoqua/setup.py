#
# This code was developed by frePPLe bv for Evoqua.
#
# Evoqua has full copyright and intellectual property rights.
# FrePPLe reserves the rights to apply the techniques and
# reuse the code for other implementations.
#

import os
import setuptools

with open(os.path.join(os.path.dirname(__file__), "__init__.py")) as initfile:
    exec(initfile.read(), globals())

setuptools.setup(
    name="evoqua",
    description="frePPLe extension module for Evoqua",
    author="frepple.com",
    author_email="jdetaeye@frepple.com",
    version=__version__,
    packages=["evoqua", ],
    package_dir={"evoqua": "."},
    package_data={
        "": ["templates/**/*"],
    },
    include_package_data=True,
    zip_safe=False,
)
