from reportlab.pdfgen import canvas


pdf_path = "artifacts/test.pdf"


c = canvas.Canvas(pdf_path)


c.drawString(
    100,
    750,
    "OM AI PDF Intelligence Test"
)


c.drawString(
    100,
    700,
    "Revenue Q1: 50000"
)


c.drawString(
    100,
    650,
    "Revenue Q2: 75000"
)


c.drawString(
    100,
    600,
    "Technology: Artificial Intelligence"
)


c.save()


print("Created:", pdf_path)
