import pytest
from carpe_pdf import PDF
from error import *

""" TEST CASE """


# For normal pdf
def test_normal_check():
    pdf = PDF('../samples/normal.pdf')
    # assert pdf.check()


def test_normal_parse():
    pdf = PDF('../samples/normal.pdf')
    assert pdf.parse()


def test_normal_content():
    pdf = PDF('../samples/normal.pdf')
    pdf.parse_content()
    assert pdf.content  # For sequences, (strings, lists, tuples), use the fact that empty sequences are false.


def test_normal_metadata():
    pdf = PDF('../samples/normal.pdf')
    pdf.parse_metadata()
    assert pdf.metadata  # For sequences, (strings, lists, tuples), use the fact that empty sequences are false.