from os.path import isfile
from markdown import markdown

__all__ = ['default', 'rules', 'settings', 'docs']


def render_md(md_file):
    if not isfile(md_file):
        return ''
    return return_md("".join(open(md_file, "r").readlines()).decode("utf-8"))


def return_md(md_input):
    return markdown(md_input, extensions=['meta', 'extra', 'fenced_code', 'tables', 'codehilite', 'toc', 'attr_list'])
