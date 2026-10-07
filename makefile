cls:
	clear

compiler:
	python3 setup.py build_ext --inplace

uninstall:
	pip3 uninstall -y stylecord.py

install:
	pip3 install .

git-%:
	git add .
	git commit -m "$*"
	git push origin main

all: cls compiler uninstall install