MAKE = make


.PHONY: docs, commit, docs.html, docs.commit, always

docs: docs.html docs.commit

docs.html: always
	$(MAKE) -C docs html

docs.commit: always
	git add docs
	git commit -m "[docs] /build"

commit: docs

always: