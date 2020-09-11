import pytest
from carpe_pdf import PDF
from error import *

""" TEST CASE """


# For damaged pdf
def test_damaged_check():
    pdf = PDF('../samples/damaged.pdf')
    assert not pdf.check()


def test_damaged_parse():
    pdf = PDF('../samples/damaged.pdf')
    assert not pdf.parse()


def test_damaged_content():
    pdf = PDF('../samples/damaged.pdf')
    pdf.parse_content()
    assert pdf.content


def test_damaged_kor_content():
    pdf = PDF('../samples/damaged_kor.pdf')  # PDF 1.7
    pdf.parse_content()
    assert pdf.content


def test_damaged_kor_6_content():
    pdf = PDF('../samples/damaged_kor_1_6.pdf')  # PDF 1.6
    pdf.parse_content()
    assert pdf.content


def test_damaged_kor_5_content():
    pdf = PDF('../samples/damaged_kor_1_5.pdf')  # PDF 1.5
    pdf.parse_content()
    assert pdf.content


def test_damaged_kor_4_content():
    pdf = PDF('../samples/damaged_kor_hwp.pdf')  # PDF 1.4
    pdf.parse_content()
    assert pdf.content


def test_damaged_kor_3_content():
    pdf = PDF('../samples/damaged_kor_1_3.pdf')  # PDF 1.3
    pdf.parse_content()
    assert pdf.content


def test_damaged_font_kor_eng_7():
    pdf = PDF('../samples/damaged_font.pdf')
    pdf.parse_content()
    assert pdf.content