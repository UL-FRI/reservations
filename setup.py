import os.path

import setuptools

# Get the long description from README.
with open("README.rst", "r") as fh:
    long_description = fh.read()

# Get package metadata from '__about__.py' file.
about = {}
base_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(base_dir, "src", "reservations", "__about__.py"), "r") as fh:
    exec(fh.read(), about)

setuptools.setup(
    name=about["__title__"],
    use_scm_version=True,
    description=about["__summary__"],
    long_description=long_description,
    long_description_content_type="text/x-rst",
    author=about["__author__"],
    author_email=about["__email__"],
    url=about["__url__"],
    license=about["__license__"],
    # Exclude tests from built/installed package.
    packages=setuptools.find_packages(
        exclude=["tests", "tests.*", "*.tests", "*.tests.*"]
    ),
    package_dir={"": "src"},
    package_data={"reservations": []},
    python_requires=">=3.10, <3.11",
    install_requires=[
        "Django~=4.1.0",
        "django-guardian~=2.4.0",
        "djangorestframework~=3.14.0",
        "django-filter~=22.1",
    ],
    extras_require={
        "package": [
            "twine",
            "wheel",
        ],
        "test": [
            "black>=22.10.0",
            "coverage>=6.5.0",
            "flake8>=5.0.4",
            "pydocstyle>=6.1.1",
            "readme_renderer",
            "setuptools_scm",
            "isort>=5.10.1",
            "django-debug-toolbar",
            "ipython",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
    ],
    keywords="FRI reservations django",
)
