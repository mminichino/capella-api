.PHONY:	setup push pypi patch minor major
export PYTHONPATH := $(shell pwd)/tests:$(shell pwd):$(PYTHONPATH)
export PROJECT_NAME := $$(basename $$(pwd))
export PROJECT_VERSION := $(shell cat VERSION)

commit:
		git commit -am "Version $(shell cat VERSION)"
		git push -u origin main
patch:
		bumpversion --allow-dirty patch
minor:
		bumpversion --allow-dirty minor
major:
		bumpversion --allow-dirty major
pypi:
		poetry build
		poetry publish
build:
		poetry build
publish:
		poetry publish
test:
		python -m pytest \
		tests/test_1.py \
		tests/test_2.py \
		tests/test_3.py \
		tests/test_4.py \
		tests/test_5.py
test_user:
		python -m pytest tests/test_2.py
test_project:
		python -m pytest tests/test_3.py
test_database:
		python -m pytest tests/test_4.py
test_columnar:
		python -m pytest tests/test_5.py
