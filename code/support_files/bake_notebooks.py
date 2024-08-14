from html.parser import HTMLParser
import os, re, argparse, json
import shutil


def clean_unsolved_notebook(nb_file):
    """Modify notebook file for distribution to students

    1. Remove outputs from code cells
    2. Remove the answers from exercise cells
    """
    nb_data = json.load(open(nb_file, encoding="utf-8"))

    for i,cell in enumerate(nb_data['cells']):
        # remove outputs from all code cells
        if cell['cell_type'] == 'code':
            remove_output_from_code(cell)

        # remove answers from exercise cells
        if cell['cell_type'] == 'markdown':
            cls = get_cell_class(cell)
            if cls == 'exercise':
                # we don't know how many solution code cells there are,
                # so send the entire list of remaining cells to the function
                # and let it decide how many to clean
                remove_answers_from_exercise(nb_data['cells'][i+1:])

    # Write changes back to notebook
    with open(nb_file, 'w', encoding="utf-8") as fh:
        json.dump(nb_data, fh, indent=2)


def update_styles_in_notebook(nb_file):
    """Update styles in markdown cells in notebook file
    
    All markdown cells must start with a <div class=...> tag.
    The style of the cell is set based on the class attribute.

    We do this because there is not a reliable way to define CSS class
    styles in notebooks; we must manually set the style of each cell.
    """
    nb_data = json.load(open(nb_file, encoding="utf-8"))
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
    with open(nb_file, 'w', encoding="utf-8") as f:
        f.write(nb_json)


def remove_output_from_code(cell):
    """Remove outputs from code cell (inplace)"""
    cell['outputs'] = []
    cell['metadata'] = {}
    cell['execution_count'] = None


def remove_answers_from_exercise(cells):
    """Remove answers from the code cell(s) following an exercise markdown cell

    The rules here are:
    - The exercise markdown cell is followed by 0 or more solution code 
      cells with no markdown cells in between. Thus, we process only the code cells in 
      *cells* until the first non-code cell.
    - Any line in a code cell that starts with "###" marks the beginning or end of the
      solution code to remove. This may happen multiple times in a single cell. For example::

        # Here is some setup code provided to the student
        # (we keep this code)

        ### Your code here:
        # This is the solution code to be removed

        ### Check your results:
        # We provide some code here to check the student's solution
        # (we keep this code as well)
      
    - Removed code blocks are replaced by 2 empty lines.
    - If there is only one solution code cell and it does not contain any "###" lines,
      then all code in that cell is removed (this is so that the vast majority of single-cell
      solutions don't need to be marked with "###")

    Processed code cells are removed from the list.
    """
    code_cells = []
    while len(cells) > 0 and cells[0]['cell_type'] == 'code':
        code_cells.append(cells.pop(0))

    # remove solution code between "###" lines
    saw_marker = False
    for cell in code_cells:
        in_solution = False
        source_lines, cell['source'] = cell['source'], []
        for line in source_lines:
            # does this line start a new solution or end the current one?
            solution_marker = line.startswith('###')
            if solution_marker:
                saw_marker = True
                in_solution = not in_solution

            # Keep only lines that are not part of the solution
            if not in_solution or solution_marker:
                cell['source'].append(line)

            # if we just entered a solution, add two blank lines
            if in_solution and solution_marker:
                cell['source'].extend(['\n', '\n'])            

    # special case: if there is only one solution cell and no "###" lines, remove all code
    if not saw_marker and len(code_cells) == 1:
        code_cells[0]['source'] = []
    

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
    
    if len(source_lines) == 0:
        # Cell is empty, nothing to do
        return

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


# def replace(new_filename, old_filename):
#     """Adjust the file paths in *new_filename* assuming that they were originally
#     written relative to *old_filename*.
    
#     Only the paths of files in the support_files directory are adjusted.
#     """
#     new_path = os.path.split(new_filename)[0]
#     old_path = os.path.split(old_filename)[0]

#     text = open(new_filename, encoding="utf-8").read()
#     with open(new_filename, 'w', encoding="utf-8") as f:
#         while True:
#             m = re.match(r'(.*["\'])([^"\']*support_files[^"\']*)(["\'].*)', text, re.DOTALL)
#             if m is None:
#                 f.write(text)
#                 break
#             pre, old_support_path, post = m.groups()            
#             new_support_path = os.path.relpath(os.path.join(old_path, old_support_path), new_path)
#             print(f'  adjusting path: {old_support_path} -> {new_support_path}')
#             f.write(pre + new_support_path)
#             text = post


def replace(filename, search, replace):
    text = open(filename, encoding="utf-8").read()
    text = text.replace(search, replace)
    with open(filename, 'w', encoding="utf-8") as f:
        f.write(text)


def render_html(nb_file):
    """Render html from notebook file"""
    path, filename = os.path.split(nb_file)
    name, ext = os.path.splitext(filename)
    html_path = os.path.join(path, 'html')
    os.system(f'jupyter nbconvert --to html --output-dir {html_path} {nb_file}')

    # adjust support file paths
    html_file = os.path.join(html_path, name + '.html')
    replace(html_file, 'support_files', '../support_files')


def run_notebook(nb_file):
    """Rerun notebook to ensure that it is working
    
    The entire notebook is executed regardless of errors."""
    os.system(f'jupyter nbconvert --execute --to notebook --allow-errors --inplace {nb_file}')


def check_notebook_errors(nb_file):
    """Check for cell outputs that contain an error,
    unless the last line of the code cell contains "raises an exception"
    """
    nb_data = json.load(open(nb_file, encoding="utf-8"))
    for cell in nb_data['cells']:
        if cell['cell_type'] != 'code' or 'raises an exception' in cell['source'][-1].lower():
            continue
        for output in cell['outputs']:
            if output['output_type'] == 'error':
                raise ValueError(f"Error in cell {cell['execution_count']}: {output['evalue']}")


def bake_all_notebooks(nb_files):
    """Bake all notebooks in *nb_files* for distribution to students"""
    for nb_file in nb_files:
        if not nb_file.endswith('_solutions.ipynb'):
            raise ValueError(f'Notebook filename must end with "_solutions.ipynb"')
        path, filename = os.path.split(os.path.abspath(nb_file))
        filename, _, ext = filename.partition('_solutions')
        parent = os.path.split(path)[0]
        unsolved_nb_file = os.path.join(parent, filename + ext)

        print("Processing", nb_file)

        # Update styles in markdown cells then rerun / test the notebook
        print("  updating markdown styles")
        update_styles_in_notebook(nb_file)

        # Create unsolved version of the notebook
        print(f'  creating unsolved notebook {unsolved_nb_file}')
        shutil.copyfile(nb_file, unsolved_nb_file)
        # adjust support file paths
        replace(unsolved_nb_file, '../support_files', 'support_files')

        # test original notebook
        print('  running solved notebook')
        run_notebook(nb_file)
        print('  checking for errors')
        check_notebook_errors(nb_file)

        # test again on unsolved notebook since we have changed file paths
        print('  running unsolved notebook')
        run_notebook(unsolved_nb_file)
        print('  checking for errors')
        check_notebook_errors(unsolved_nb_file)

        # remove outputs from code cells and answers from exercise cells
        print("  cleaning unsolved notebook")
        clean_unsolved_notebook(unsolved_nb_file)

        # Render html from original solution file
        print("  rendering html")
        render_html(nb_file)


description = """
This script modifies notebooks for distribution to students:

1. Sanity check html in all markdown cells
   - Require that all markdown cells start with a <div class=...> tag
   - Ensure that html tags are matched (to avoid rendering errors)
2. Add styles to all markdown cells based on the opening <div> tag's class
   So for example <div class="exercise"> becomes <div class="exercise" style="...">
3. Rerun the notebook to ensure that it is working
   - Check for errors in cell outputs
     (unless the last line of the code cell contains "raises an exception")
4. Create an unsolved version of the notebook:
   - Adjust resource file names to correct path
   - Run this new notebook to ensure it works in its new location
   - Remove outputs from code cells
   - Remove the answers from exercise cells
     (answers are marked by lines starting with "###"; see code for details)
5. Render original solution files to html

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
