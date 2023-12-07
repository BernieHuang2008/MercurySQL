MAKE = make


.PHONY: docs, commit, docs.html, docs.commit, always

docs: docs.html docs.commit

docs.html: always
	$(MAKE) -C docs html

docs.commit: always
	git add docs
	git commit -m "[docs] /build"

docs.clear: always
	git checkout -- docs/build

commit: docs

venv: always
	.venv\Scripts\activate 

always: