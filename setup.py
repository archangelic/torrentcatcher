#!/usr/bin/env python
from setuptools import setup

setup(
	name = "torrentcatcher",
	version = "1.1.1",
	dependency_links = ['http://www.voidspace.org.uk/downloads/validate.py#egg=validate-1.0.1'],
	install_requires = ['configobj>=4.7.0', 'argparse>=1.2.1', 'validate>=1.0.1', 'feedparser>=5.1.3', 'tabulate>=0.7.3'],
)
