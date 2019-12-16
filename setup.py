from setuptools import setup, find_packages

reqs = [
    x.strip() for x
    in open('requirements.txt').readlines() if not x.startswith('#')
]

setup(
    name='nba-heat-check',
    version='1.0',
    packages=find_packages(),
    install_requires=reqs,
    entry_points={
        'console_scripts': [
            'main = main:main'
        ],
    }
)
