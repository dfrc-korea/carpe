import pytest
from carpe_pdf import PDF
from error import *

""" TEST CASE """


# For PDF Class
def test_pdf():
    with pytest.raises(PDFOpenError):
        pdf = PDF('')


def test_print_content():
    pdf = PDF('../samples/normal.pdf')
    pdf.parse_content()
    # pdf.print_content()


def test_print_metadata():
    pdf = PDF('../samples/normal.pdf')
    pdf.parse_metadata()
    # pdf.print_metadata()





