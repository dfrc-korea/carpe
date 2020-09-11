# READ(REpair dAmaged Document)

> A kind of data recovery project in Carpe Forensics

- Main Target
	- Open Office XML(OOXML)
	- Compound File Binary Format(MS Office)
	- Portable Document Format(PDF)
	- Compound File Binary Format(Hancom)

## PDF
> Very nice PDF string extraction python library

### Prerequisites

* Python 3.6 or later
* [pdfminer](https://github.com/euske/pdfminer)

### Usage

**Create PDF object**

	from carpe_pdf import PDF
	...
	pdf = PDF('path/to/pdf')

**Restore PDF body content**

	pdf.parse_content()

**Restore PDF metadata**

	pdf.parse_metadata()


- Test Sample

- Test Result
