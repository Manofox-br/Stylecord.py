import sys, select, argparse
from setuptools import setup, find_packages, Extension
from Cython.Build import cythonize

#===| ASSISTANTS|===#
parser = argparse.ArgumentParser(description="Custom installer")
parser.add_argument("-y", "--yes", action="store_true")
parser.add_argument("-n", "--no", action="store_true")
args, unknown = parser.parse_known_args()

default = "no"
n = ["n", "no"]
y = ["y", "yes"]

libs = [
    "picows>=2.3.1",
    "httpx>=0.28.1",
    "cython>=3.3.0"
]
extra_libs = {
    "colors": ["webcolors>=25.10.0"]
}

chosen_extras = [arg for arg in sys.argv if arg in extra_libs]

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

# funcs
def timed_input(prompt, timeout=10):
    print(f"{prompt} (y/n) [default={default} in {timeout}s]: ", end="", flush=True)
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    if ready:
        return sys.stdin.readline().strip().lower() or default
    else:
        print()
        return default

def install_lib(lib:str):
    if not lib in libs:
        return
    
    if args.yes:
        choice = "y"
    elif args.no:
        choice = "n"
    else:
        choice = timed_input(f"Do you want to install support for color names ({lib})?", 10, "n")

    if choice in y:
        libs.append(lib)
        print(f"\033[32mAdd lib\033[0m ({lib}).")
    else:
        print(f"\033[33m[WARNING] Installation ignored\033[0m ({lib}).")

#===| LOGICS |===#
for c in chosen_extras:
    libs.append(c)
install_lib("webcolors")

#===| CONSTRUCT AND SETUP |===#
setup(
    name="stylecord.py",
    version="0.1.0",
    description="A Python library for styling and integration.",
    #long_description=open("docs/README.md").read(),
    #long_description_content_type="text/markdown",
    #url="https://www.github.com/Manofox-br/pyfusion",
    author="Manofox-br",
    license="MIT",

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
    
    python_requires=">=3.8",
    install_requires=libs,
    extras_require=extra_libs
)