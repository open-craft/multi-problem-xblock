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

#### Install in development mode in tutor

* Clone this repository somewhere locally, for example: `/path/to/multi-problem-xblock`.
* Mount this directory in tutor using `tutor mounts add /path/to/multi-problem-xblock`
* Run `tutor dev launch`

### Enabling in Studio

Go to `Settings -> Advanced` Settings and add `multi-problem` to `Advanced Module List`.

### Usage

* Click on `Advanced block` in studio unit authoring page and select `Multi Problem Block`.
* Click on `Edit` button to select a library from which child problems needs to be fetched.
* You can update the number of problems user will see using `Count` field, update cut-off score, display name etc.
* `Display feedback` field allows authors to control when users can see problem answers, this updates `show_correctness` of all the child problems.

#### Screenshots

![image](https://github.com/user-attachments/assets/b6cec90d-307b-43f8-856f-6cd54f28918a)

![image](https://github.com/user-attachments/assets/645b5ab4-74e9-4237-be87-c81b3d432fdf)

![image](https://github.com/user-attachments/assets/be11fe56-8c90-4f51-bce1-aa20ad852718)

![image](https://github.com/user-attachments/assets/f4243f26-c73a-4ebd-afbe-7e5bc84a9617)

![image](https://github.com/user-attachments/assets/a92831f1-df7e-40d7-a323-9c514380a3ad)


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

Multi Problem XBlock aims to comply with i18n requirements for Open edX platform, including a stricter set of
requirements for `edx.org` itself, thus providing the required files. So far only one translation is available:

* Default English translation

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
