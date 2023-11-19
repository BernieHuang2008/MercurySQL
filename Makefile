.PHONY: tidy build upload

# tidy
tidy: *.db
	rm -rf *.db

# build: build.clear build.wheel
build: build.clear build.wheel

build.clear: always
	rm -rf build dist *.egg-info

build.wheel: always
	python setup.py sdist bdist_wheel

# upload: upload.pypi
upload: upload.pypi

upload.pypi: always
	twine upload dist/*

always: