import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="comiola",
    version="1.0.0",
    description="Authoring tool to turn comics into .mp4 videos",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://alcramer@bitbucket.org/alcramer/comiola.git",
    author="Al Cramer",
    author_email="ac2.71828@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
    ],
    packages=["comiola"],
    include_package_data=True,
    install_requires=["Pillow", "imageio"],
    entry_points={
        "console_scripts": [
            "comiola=comiola:main",
        ]
    },
)

