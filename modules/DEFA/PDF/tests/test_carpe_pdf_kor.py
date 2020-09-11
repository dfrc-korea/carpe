import pytest
from carpe_pdf import PDF


""" TEST CASE """
def test_normal_kor_7_content():
    pdf = PDF('../samples/normal_kor.pdf')  # PDF 1.7 (KOR)
    pdf.parse_content()
    assert pdf.content

def test_normal_kor_6_content():
    pdf = PDF('../samples/normal_kor_1_6.pdf')  # PDF 1.6 (KOR) => ezPDF Builder Supreme
    pdf.parse_content()
    assert pdf.content

def test_normal_kor_5_content():
    pdf = PDF('../samples/normal_kor_1_5.pdf')  # PDF 1.5 (KOR)
    pdf.parse_content()
    assert pdf.content

def test_normal_kor_4_content():
    pdf = PDF('../samples/normal_kor_1_4.pdf')  # PDF 1.4 (KOR)
    pdf.parse_content()
    assert pdf.content

def test_normal_kor_3_content():
    pdf = PDF('../samples/normal_kor_1_3.pdf')  # PDF 1.3 (KOR)
    pdf.parse_content()
    assert pdf.content

def test_kor_eng_7_content():
    pdf = PDF('../samples/kor_eng_word.pdf')
    pdf.parse_content()
    assert pdf.content

def test_kor_7_metadata():
    pdf = PDF('../samples/normal_kor.pdf')
    pdf.parse_metadata()
    assert pdf.metadata

def test_kor_5_metadata():
    pdf = PDF('../samples/normal_kor_1_5.pdf')
    pdf.parse_metadata()
    assert pdf.metadata

def test_kor_4_metadata():
    pdf = PDF('../samples/normal_kor_1_4.pdf')
    pdf.parse_metadata()
    assert pdf.metadata

def test_kor_eng_7_metadata():
    pdf = PDF('../samples/kor_eng_word.pdf')
    pdf.parse_metadata()
    assert pdf.metadata