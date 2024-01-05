MAKE = make


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
	rm -rf .venv

venv.req: always
	$(MAKE) venv.activate
	pip install -r requirements.txt

venv.new: always
	$(MAKE) venv.clear
	python -m venv .venv
	$(MAKE) venv.req

pkg.build: always
	$(MAKE) pkg.clear
	python setup.py sdist bdist_wheel

pkg.clear: always
	rm -rf build dist *.egg-info

pkg.install: always
	pip install dist/*.whl

pkg: pkg.build pkg.install

tidy: pkg.clear docs.clear venv.clear

always: