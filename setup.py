#from distutils.core import setup
from setuptools import setup, find_packages
setup(
  name = 'adt_pulse_client',
  py_modules = ['adt_pulse_client'],
  version = '0.1',
  description = 'Interact with ADT Pulse alarm systems',
  author = 'Jeroen A. Goddijn',
  author_email = 'mariniertje@gmail.com',
  url = 'https://github.com/mariniertje/adt_pulse_client',
  download_url = 'https://github.com/mariniertje/adt_pulse_client',
  keywords = ['alarm','ADTPulse'],
  package_data = {'': ['data/*.json']},
  requires = ['zeep', 'pprint', 'logging', 'logging.handlers', 'sys'],
  install_requires = ['zeep'],
#  packages=find_packages(exclude=['tests', 'tests.*']),
  packages=['adt_pulse_client'],
  include_package_data=True, # use MANIFEST.in during install
  zip_safe=False
)