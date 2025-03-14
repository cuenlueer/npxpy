from setuptools import setup, find_packages
from os import path
import npxpy

with open(
    path.join(path.abspath(path.dirname(__file__)), "docs/README.md"),
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
    description="Python based open source text-only project preparation"
    " framework for Nanoscribe’s two-photon 3D lithography"
    " system Quantum X align.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["pytomlpp", "numpy-stl", "pyvista", "pyvistaqt", "numpy"],
    test_suite="tests",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Aligned 2-Photon 3D Lithography",
        "Topic :: Scientific/Engineering :: Physics",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
