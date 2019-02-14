from setuptools import setup

setup(name='synpuf',
      version='0.1',
      description='Python package for synthesizing a distributable version of the IRS Public Use File, and evaluating this synthesis for fidelity and privacy.',
      url='http://github.com/donboyd5/synpuf',
      author='Max Ghenis',
      author_email='mghenis@gmail.com',
      license='MIT',
      packages=['synpuf'],
      install_requires=[
          'numpy',
          'pandas',
          'synthimpute',
          'rpy2'
      ],
      zip_safe=False)
