MAKE = make

ifeq ($(OS),Windows_NT)
	DEL = del /S /Q
	PIP = pip
else
	DEL = rm -rf
	PIP = pip3
endif


.PHONY: docs, commit, docs.html, docs.commit, always

docs: docs.html docs.commit

docs.html: always
	$(MAKE) -C docs html

docs.commit: always
	git add docs
	git commit -m "[docs] /build"

docs.clear: always
	git checkout --force -- docs/build

commit: docs

venv.activate: always
	.venv\Scripts\activate.bat

venv.clear: always
	$(DEL) .venv

venv.req: always
	$(MAKE) venv.activate
	$(PIP) install -r requirements.txt

venv.new: always
	$(MAKE) venv.clear
	python -m venv .venv
	$(MAKE) venv.req

pkg.build: always
	$(MAKE) pkg.clear
	python setup.py sdist bdist_wheel

pkg.clear: always
	$(DEL) build dist *.egg-info

pkg.install: always
	$(PIP) install dist/*.whl --force-reinstall

pkg: pkg.build pkg.install

tidy: pkg.clear docs.clear venv.clear

always: