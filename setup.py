from setuptools import setup

version = '0.1.0'
long_description = 'Command Line Client for FireCloud'

setup(
  name='firecloudcli',
  version=version,
  description=long_description,
  author='DSDE Engineering',
  author_email='dsde-engineering@broadinstitute.org',
  zip_safe = False,
  install_requires=[
      'httplib2','google-api-python-client'
  ],
  packages = ['firecloudcli'],
  license = 'BSD',
  keywords = 'CLI, FireCloud',
  url = 'http://github.com/broadinstitute/firecloudcli',
  classifiers=[
      'License :: OSI Approved :: BSD License',
      'Programming Language :: Python',
      'Development Status :: 4 - Beta',
      'Intended Audience :: Developers',
      'Natural Language :: English'
  ],
  entry_points = {
        'console_scripts': [
            'firecloud = firecloudcli.main:main',
            'methods_repo = firecloudcli.methods_repo:main'
        ],
    }
)