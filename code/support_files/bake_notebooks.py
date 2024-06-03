import glob
from html.parser import HTMLParser
import os, sys, re, argparse, json

from xml.etree import ElementTree


def make_unsolved_notebook(nb_file):
    """Modify and copy solution notebook file

    1. Remove the answers from exercise cells
    2. Adjust resource file names to correct path
    3. Write modified notebook to parent directory
    """
    nb_data = json.load(open(nb_file))

    # remove answers from exercise cells
    last_md_cell_is_exercise = False
    for cell in nb_data['cells']:
        if cell['cell_type'] == 'code' and last_md_cell_is_exercise:
            remove_answers(cell)

        if cell['cell_type'] == 'markdown':
            cls = get_cell_class(cell)
            last_md_cell_is_exercise = cls == 'exercise'
        else:
            last_md_cell_is_exercise = False

    # Correct resource file paths
    nb_json = json.dumps(nb_data, indent=2)
    nb_json = adjust_file_paths(nb_json)

    # Write modified notebook to parent directory
    path, filename = os.path.split(os.path.abspath(nb_file))
    filename, _, ext = filename.partition('_solutions')
    parent = os.path.split(path)[0]
    new_file = os.path.join(parent, filename + ext)
    with open(new_file, 'w') as f:
        f.write(nb_json)


def update_styles_in_notebook(nb_file):
    """Update styles in markdown cells in notebook file
    
    All markdown cells must start with a <div class=...> tag.
    The style of the cell is set based on the class attribute.

    We do this because there is not a reliable way to define CSS class
    styles in notebooks; we must manually set the style of each cell.
    """
    nb_data = json.load(open(nb_file))
    for cell in nb_data['cells']:
        if cell['cell_type'] != 'markdown':
            continue

        try:
            # check html in markdown cells
            checker = CellHtmlChecker()
            checker.feed(''.join(cell['source']))

            # set style of markdown cell based on class
            set_md_style(cell['source'])
        except ValueError as e:
            raise ValueError(f"Error in cell:\n\n{''.join(cell['source'])}") from e

    # Overwrite notebook with modified styles 
    nb_json = json.dumps(nb_data, indent=2)
    with open(nb_file, 'w') as f:
        f.write(nb_json)


class CellHtmlChecker(HTMLParser):
    """HTML parser that ensures all tags are matched
    """
    no_match_tags = ['p', 'li', 'td', 'img', "br", "hr", 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']

    def __init__(self):
        super().__init__()
        self.stack = []
        self.outer_tag = None

    def feed(self, data, check=True):
        super().feed(data)
        if check and len(self.stack) > 0:
            raise ValueError(f'Unclosed tags: {self.stack}')

    def handle_starttag(self, tag, attrs):
        if tag in self.no_match_tags:
            return
        if len(self.stack) == 0:
            self.outer_tag = tag, attrs
        self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.no_match_tags:
            return
        if len(self.stack) == 0:
            raise ValueError(f'Closing tag <{tag}> with no opening tag')
            
        last_tag = self.stack.pop()
        if last_tag != tag:
            raise ValueError(f'Closing tag <{tag}> while still inside <{last_tag}>')


def get_cell_class(cell):
    """Get class of markdown cell"""
    parser = CellHtmlChecker()
    parser.feed(''.join(cell['source']))
    if parser.outer_tag is None or parser.outer_tag[0] != 'div':
        raise ValueError('Markdown cell must start with a <div cell=...> tag')
    tag, attrs = parser.outer_tag
    attrs = dict(attrs)
    if 'class' not in attrs:
        raise ValueError('Markdown cell <div> tag must have class attribute')
    return attrs['class']


def set_md_style(source_lines):
    """Set style of markdown cell based on class"""
    global styles

    m = re.match(r'^<div([^>]*)>', source_lines[0])
    if m is None:
        raise ValueError('Markdown cell opening line must start with <div class="...">')

    parser = CellHtmlChecker()
    parser.feed(m.group(0), check=False)
    tag, attrs = parser.outer_tag
    attrs = dict(attrs)

    md_class = attrs.get('class', 'default')
    if md_class not in styles:
        raise ValueError('Unknown class in markdown cell: ' + md_class)
    source_lines[0] = f'<div class="{md_class}" style="{styles[md_class]}">' + source_lines[0][len(m.group(0)):]


def adjust_file_paths(text, parent=True):
    if parent:
        return re.sub(r'\.\./support_files/', 'support_files/', text)
    else:
        return re.sub(r'\.\./support_files/', '../../support_files/', text)


def remove_answers(cell):
    """Remove answers from exercise code cells
    
    Optionally, some starter code may be provided if it ends with "# Your code here:\n"
    """
    source = ''.join(cell['source'])
    parts = source.partition('# Your code here:\n')
    if parts[1] == '':
        cell['source'] = ''
    else:
        cell['source'] = (parts[0] + parts[1]).splitlines(keepends=True)
    cell['outputs'] = []


def render_html(nb_file):
    """Render html from notebook file"""
    path, filename = os.path.split(nb_file)
    name, ext = os.path.splitext(filename)
    html_path = os.path.join(path, 'html')
    os.system(f'jupyter nbconvert --to html --output-dir {html_path} {nb_file}')
    html_file = os.path.join(html_path, name + '.html')
    with open(html_file, 'r') as f:
        html = f.read()
    html = adjust_file_paths(html, parent=False)
    with open(html_file, 'w') as f:
        f.write(html)


def rerun_notebook(nb_file):
    """Rerun notebook to ensure that it is working
    
    The entire notebook is executed regardless of errors."""
    os.system(f'jupyter nbconvert --execute --to notebook --allow-errors --inplace {nb_file}')


def check_notebook_errors(nb_file):
    """Check for cell outputs that contain an error,
    unless the last line of the code cell contains "raises an exception"

    """
    nb_data = json.load(open(nb_file))
    for cell in nb_data['cells']:
        if cell['cell_type'] != 'code' or 'raises an exception' in cell['source'][-1].lower():
            continue
        for output in cell['outputs']:
            if output['output_type'] == 'error':
                raise ValueError(f'Error in cell {cell['execution_count']}: {output['evalue']}')


def bake_all_notebooks(nb_files):
    """Bake all notebooks in a directory"""
    for file in nb_files:
        print("Processing", file)
        print("  updating markdown styles")
        update_styles_in_notebook(file)
        print('  rerunning notebook')
        rerun_notebook(file)
        print('  checking for errors')
        check_notebook_errors(file)
        print("  making unsolved notebook")
        make_unsolved_notebook(file)
        print("  rendering html")
        render_html(file)



description = """
This script modifies notebooks for distribution to students:

- Sanity check html in all markdown cells
    - Ensure that all markdown cells are valid xml
    - Require that all markdown cells start with a <div class=...> tag
- Add styles to all markdown cells based on class
- Rerun the notebook to ensure that it is working
- Check for errors in cell outputs
- Create an unsolved version of the notebook:
    - Remove the answers from exercise cells
      (one code cell following each exercise markdown cell; 
      may contain starter code if it ends with "# Your code here:\\n")
    - Adjust resource file names to correct path
- Render original solution files to html

"""


styles = {
    'default': "border-left: 3px solid #000; padding: 1px; padding-left: 10px; background: #F0FAFF; color: #000;",
    'exercise': "background: #DFF0D8; border-radius: 3px; padding: 10px; color: #000;",
}


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('files', help='Notebook files to bake', nargs='+')
    args = parser.parse_args()

    bake_all_notebooks(args.files)
