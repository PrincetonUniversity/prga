# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

# import os
# import sys
# sys.path.insert(0, os.path.abspath('../../prga.py'))

# -- Project information -----------------------------------------------------

project = 'Princeton Reconfigurable Gate Array'
copyright = '2019, Ang Li'
author = 'Ang Li'

# The full version, including alpha/beta/rc tags
release = 'Alpha 0.3.3'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.napoleon',
    'sphinx.ext.autodoc',
    'sphinx.ext.githubpages',
    'sphinx.ext.autosectionlabel',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Master document containing the root toctree
master_doc = "index"

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_materialdesign_theme'
html_logo = '_static/images/logo.png'
html_theme_options = {
        'header_links' : [
            ('Home', 'http://parallel.princeton.edu/prga/', True, 'home'),
            ('Github', "https://github.com/PrincetonUniversity/prga", True, 'link'),
            ('Documentation', "index", False, 'description'),
            ], 
        'fixed_drawer': True,
        'fixed_header': True,
        'header_waterfall': True,
        'header_scroll': False,
        'show_header_title': False,
        'show_drawer_title': True,
        'show_footer': True,
        }

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# -- Extension configuration -------------------------------------------------
default_role = 'any'

autodoc_default_options = {
        'member-order': 'bysource',
        'private-members': None,
        'ignore-module-all': None,
        'exclude-members': '_abc_cache,_abc_negative_cache,_abc_negative_cache_version,_abc_registry,_abc_impl',
        }

# Napoleon settings
napoleon_google_docstring = True
