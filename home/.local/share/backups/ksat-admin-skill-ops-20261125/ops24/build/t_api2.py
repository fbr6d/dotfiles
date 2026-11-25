import pymupdf
from pymupdf import mupdf
names = [n for n in dir(mupdf) if ('font' in n.lower()) and ('pdf_' in n) and not n.startswith('ll_')]
print(len(names)); print(' '.join(names))
print([n for n in dir(mupdf) if 't3' in n.lower() and not n.startswith('ll_')][:40])
