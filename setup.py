import setuptools
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

scriptDir = os.path.abspath(os.path.dirname(__file__))
version = "0.0.1"
if os.path.exists(f'{scriptDir}/version'):
    with open(f'{scriptDir}/version', 'r') as f:
        version = f.read()

setuptools.setup(
    name="jinny",
    version=version,
    author="Andrew Southall",
    author_email="bots@trulydigital.net",
    description="A practical templating tool for Jinja templates",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/scripteddog/jinny",
    project_urls={
        "Source": "https://github.com/smashthings/jinny"
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Other",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    keywords="jinja,template,jinja2,kubernetes",
    license="GPLv3",
    entry_points={
        'console_scripts': [
            'jinny=jinny.jinny:Main',
        ],
    }
)