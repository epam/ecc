from setuptools import find_packages, setup
from c7ncli.version import __version__


setup(
    name='c7ncli',
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click==7.1.2',
        'tabulate==0.9.0',
        'requests==2.31.0',
        'boto3==1.26.80',
        'python-dateutil==2.8.2',
        'modular-cli-sdk[hvac]'
    ],
    entry_points='''
        [console_scripts]
        c7n=c7ncli.group.c7n:c7n
    ''',
    python_requires='>=3.10'
)
