# Multi-problem xblock

This XBlock implements a single window to display multiple problems in random
from any library of problems.

### Installation

Install the requirements into the Python virtual environment of your
`edx-platform` installation by running the following command from the
root folder:

```bash
$ pip install -r requirements.txt
```

### Enabling in Studio

Go to `Settings -> Advanced` Settings and add `multi-problem` to `Advanced Module List`.

### Usage

*TBD*

### Testing with tox

Inside a fresh virtualenv, `cd` into the root folder of this repository
(`multi-problem-xblock`) and run:

```bash
$ make requirements
```


You can then run the entire test suite via:

```bash
$ make test
```

To run specific test groups, use one of the following commands:

```bash
$ make test.unit
$ make test.quality
$ make test.translations
```

To run individual unit tests, use:

```bash
$ make test.unit TEST=tests/unit/test_basics.py::BasicTests::test_student_view_data
```

### Manual testing (without tox)

To run tests without tox, use:

```bash
$ make requirements_python
$ make test.python TEST=tests/unit/test_basics.py::BasicTests::test_student_view_data
```


## i18n compatibility

According to [edX docs on XBlock i18n][edx-docs-i18n], LMS runtime is capable of supporting XBlock i18n and l10n.
To comply with l10n requirements, XBlock is supposed to provide translations in
`xblock_package_root/translations/locale_code/LC_MESSAGES/text.po` folder in GNU Gettext Portable Object file format.

[edx-docs-i18n]: http://edx.readthedocs.io/projects/xblock-tutorial/en/latest/edx_platform/edx_lms.html#internationalization-support

Drag and Drop v2 XBlock aims to comply with i18n requirements for Open edX platform, including a stricter set of
requirements for `edx.org` itself, thus providing the required files. So far only two translations are available:

* Default English translation
* Fake "Esperanto" translation used to test i18n/l10n.

Updates to translated strings are supposed to be propagated to `text.po` files. EdX [i18n_tools][edx-i18n-tools] is used here along GNU Gettext and a Makefile for automation.

[edx-i18n-tools]: https://github.com/openedx/i18n-tools

Note: currently `translations` directory is a symbolic link to `conf/locale` directory. Also, 'text.po' file for locale code `en` is a symbolic link to `conf/locale/en/LC_MESSAGES/django.po` file. Both links works as a transition step to fully moving translation files to [openedx-translations](https://github.com/openedx/openedx-translations) repository

### Translatable strings

```bash
$ make extract_translations
```

Note that this command generates `text.po` which is supposed to contain
all translatable strings.

To check if `text.po` is correct, one can run:

```bash
$ make compile_translations
```

If everything is correct, it will create `translations/en/LC_MESSAGES/text.mo` and `locale/en/LC_MESSAGES/text.js` files.

### Building fake "Esperanto" translation


As previously said, this fake translation mainly exists for testing reasons. For edX platform it is built using Dummy
translator from edX i18n-tools.

```bash
$ make dummy_translations
```

## Releasing

To release a new version, update .travis.yml and setup.py to point to your new intended version number and create a new release with that version tag via Github.
