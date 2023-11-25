MAKE = make


.PHONY: docs, docs.html, always

docs.html: always
	$(MAKE) -C docs html

always: