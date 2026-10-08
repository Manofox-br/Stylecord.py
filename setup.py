import sys, select, argparse
from setuptools import setup, find_packages, Extension
from Cython.Build import cythonize

extensions = [
    Extension(
        name="stylecord._utils.core",
        sources=["stylecord/_utils/core.pyx"]
    ),
    Extension(
        name="stylecord._utils.restapi",
        sources=["stylecord/_utils/restapi.pyx"]
    )
]

#===| CONSTRUCT AND SETUP |===#
setup(
    name="stylecord.py",
    version="0.1.3",
    description="A Discord library focused on balancing simplicity, ease of use, and performance.",
    long_description=open("docs/README.md").read(),
    long_description_content_type="text/markdown",
    url="https://www.github.com/Manofox-br/Stylecord.py",
    author="Manofox-br",
    #license="MIT",

    ext_modules=cythonize(extensions),
    packages=find_packages(include=[
        "stylecord",
        "stylecord.*",
        "stylecord._utils",
        "stylecord._utils.*",
        "stylecord.errors",
        "stylecord.errors.*"
    ]),
    package_data={"stylecord._utils": ["*.so"  "*.py"]},
    include_package_data=True,
    
    python_requires=">=3.8"
    #install_requires=libs,
    #extras_require=extra_libs
)