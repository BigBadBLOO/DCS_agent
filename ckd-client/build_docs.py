import os
import pydoc
import sys

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: {} /path/to/py/project'.format(os.path.split(__file__)[-1]))
        exit(-1)

    path = sys.argv[1]

    docs_dir = os.path.join(os.path.split(__file__)[0], 'doc')
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)
    os.chdir(docs_dir)

    pydoc.writedocs(path)

    try:
        html = '.'.join([os.path.split(__file__)[-1].split('.')[0], 'html'])
        os.remove(html)
    except FileNotFoundError:
        pass
