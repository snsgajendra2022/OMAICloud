from om_ai.perception.document.pdf.manager import PDFManager


pdf = PDFManager()


result = pdf.process(
    "artifacts/test.pdf"
)


print(result)