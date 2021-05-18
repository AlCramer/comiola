import os
from setuptools import setup

HERE = os.path.abspath(os.path.dirname(__file__))
with open('%s/README.md' % HERE,"r") as fp:
    README = fp.read()

# This call to setup() does all the work
setup(
    name="comiola",
    version="0.1",
    description="Authoring tool to turn comics into .mp4 videos",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://alcramer@bitbucket.org/alcramer/comiola.git",
    author="Al Cramer",
    author_email="ac2.71828@gmail.com",
    license="MIT",
    keywords='animation video comics',
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    packages=["comiola"],
    include_package_data=True,
    install_requires=["Pillow", "imageio", "imageio-ffmpeg"],
)

