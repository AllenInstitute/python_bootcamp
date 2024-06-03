import glob
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
        if cell['cell_type'] == 'markdown':
            tree = get_markdown_xml(cell['source'])
            last_md_cell_is_exercise = tree.attrib['class'] == 'exercise'
        else:
            last_md_cell_is_exercise = False

        if cell['cell_type'] == 'code' and last_md_cell_is_exercise:
            remove_answers(cell)

    # Correct resource file paths
    nb_json = json.dumps(nb_data, indent=2)
    nb_json = adjust_file_paths(nb_json)

    # Write modified notebook to parent directory
    path, filename = os.path.split(os.path.abspath(nb_file))
    parent = os.path.split(path)[0]
    new_file = os.path.join(parent, filename)
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
        tree = get_markdown_xml(cell['source'])
        set_md_style(tree)
        cell['source'] = ElementTree.tostring(tree).decode('utf-8')

    # Overwrite notebook with modified styles 
    nb_json = json.dumps(nb_data, indent=2)
    with open(nb_file, 'w') as f:
        f.write(nb_json)


def get_markdown_xml(source_lines):
    """Return xml tree from markdown cell source lines
    """
    source = ''.join(source_lines)
    try:
        return ElementTree.fromstring(source)            
    except ElementTree.ParseError as e:
        raise ValueError('Invalid XML in markdown cell:\n\n' + source) from e


def set_md_style(tree):
    """Set style of markdown cell based on class"""
    global styles

    if 'class' not in tree.attrib:
        raise ValueError('Markdown cell opening div must have class attribute')
    md_class = tree.attrib['class']
    if md_class not in styles:
        raise ValueError('Unknown class in markdown cell: ' + md_class)
    tree.attrib['style'] = styles[md_class]


def adjust_file_paths(text):
    return re.sub(r'\.\./support_files/', 'support_files/', text)


def remove_answers(cell):
    """Remove answers from exercise code cells
    
    Optionally, some starter code may be provided if it ends with "# Your code here:\n"
    """
    parts = cell['source'].partition('# Your code here:\n')
    cell['source'] = parts[0] + parts[1]
    cell['outputs'] = []


def render_html(nb_file):
    """Render html from notebook file"""
    path, filename = os.path.split(nb_file)
    name, ext = os.path.splitext(filename)
    html_file = os.path.join(path, 'html', name + '.html')
    os.system(f'jupyter nbconvert --to html --output-dir {html_file} {nb_file}')


def rerun_notebook(nb_file):
    """Rerun notebook to ensure that it is working
    
    The entire notebook is executed regardless of errors."""
    os.system(f'jupyter nbconvert --execute --to notebook --allow-errors --inplace {nb_file}')


def check_notebook_errors(nb_file):
    """Check for cell outputs that contain an error.

    """
    nb_data = json.load(open(nb_file))
    for cell in nb_data['cells']:
        if cell['cell_type'] != 'code':
            continue
        for output in cell['outputs']:
            if output['output_type'] == 'error':
                raise ValueError(f'Error in cell {cell['execution_count']}: {output['evalue']}')


def bake_all_notebooks(path):
    """Bake all notebooks in a directory"""
    for file in glob.glob(os.path.join(path, "*.ipynb")):
        print("Processing", file)
        print("  updating markdown styles")
        update_styles_in_notebook(file)
        print('  rerunning notebook')
        rerun_notebook(file)
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

    bake_all_notebooks(args.path)
