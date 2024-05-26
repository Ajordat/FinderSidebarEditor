import pathlib
from setuptools import setup
#from finder_sidebar_editor import __version__


# The text of the README file
HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()
VERSION = "v1.2.1"

setup(
    name="finder_sidebar_editor",
    version=VERSION,
    description="Module and CLI for editing the Favorites entries of the Finder sidebar.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/Ajordat/finder-sidebar-editor",
    author="Ajordat",
    author_email="alexjortri@gmail.com",
    maintainer="Ajordat",
    maintainer_email="alexjortri@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7"
    ],
    packages=["finder_sidebar_editor"],
    include_package_data=True,
    install_requires=["pyobjc"],
    entry_points={
        "console_scripts": [
            "finder_sidebar_editor=finder_sidebar_editor.cli:app"
        ]
    }
)
