from setuptools import setup, find_packages
from os import path
import npxpy

with open(
    path.join(path.abspath(path.dirname(__file__)), "README.md"),
    encoding="utf-8",
) as f:
    long_description = f.read()

setup(
    name="npxpy",
    version=npxpy.__version__,
    author="Caghan Uenlueer, Simone Ferrari, Wolfram Pernice",
    author_email="caghan.uenlueer@kip.uni-heidelberg.de",
    project_urls={
        "Documentation": "",  # TBA
        "Bug Tracker": "https://github.com/cuenlueer/npxpy/issues",
        "Source Code": "https://github.com/cuenlueer/npxpy",
    },
    packages=find_packages(),
    platforms="All",
    python_requires=">=3.5",
    license="LGPLv3",
    description="Python package for creating NANO projects for the Nanoscribe QX.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["toml", "numpy-stl"],
    test_suite="tests",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Aligned 2-Photon 3D Lithography",
        "Topic :: Scientific/Engineering :: Physics",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
    ],
)
