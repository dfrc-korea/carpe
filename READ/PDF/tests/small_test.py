from carpe_pdf import PDF
from error import *

if __name__ == '__main__':
    with PDF('../samples/damaged_return.pdf') as pdf:
        pdf.parse_content()
        print(pdf.content)
