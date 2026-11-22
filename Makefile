MAKE = make

ifeq ($(OS),Windows_NT)
	DEL = del /S /Q
	PIP = pip
else
	DEL = rm -rf
	PIP = pip3
endif


.PHONY: docs, docs.html, commit, venv, test, pkg, pkg.build, pkg.clear, pkg.check, tidy, always

docs: docs.html

docs.html: always
	$(MAKE) -C docs html

commit: docs.html
	git add docs/source
	git commit -m "[docs] upd"

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

test: always
	python -m pytest tests -q

pkg.build: always
	$(MAKE) pkg.clear
	python -m build

pkg.clear: always
	$(DEL) build dist *.egg-info

pkg.check: pkg.build
	python -m twine check dist/*

pkg.install: always
	$(PIP) install dist/*.whl --force-reinstall

pkg: pkg.build pkg.install

tidy: pkg.clear venv.clear

always:
