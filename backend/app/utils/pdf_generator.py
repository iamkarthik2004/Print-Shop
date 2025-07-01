# app/utils/pdf_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime, timezone


def generate_summary_pdf(
        username: str,
        custom_pages: str,
        total_pages: int,
        color: bool,
        sides: str,
        orientation: str,
        amount: float,
        payment_method: str
) -> BytesIO:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50

    def draw_line(text: str):
        nonlocal y
        c.drawString(50, y, text)
        y -= 20

    draw_line(f"Print Summary Receipt")
    draw_line(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    draw_line(f"Username: {username}")
    draw_line(f"Payment Method: {payment_method}")
    draw_line(f"Pages: {custom_pages} (Total: {total_pages})")
    draw_line(f"Options: {'Color' if color else 'B/W'}, {sides}, {orientation}")
    draw_line(f"Total Amount: ₹{amount:.2f}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


def generate_payment_receipt_pdf(
        username: str,
        amount: float,
        reference_id: str
) -> BytesIO:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 80

    def draw_line(text: str):
        nonlocal y
        c.drawString(50, y, text)
        y -= 25

    draw_line("🧾 Payment Receipt")
    draw_line(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    draw_line(f"Username: {username}")
    draw_line(f"Amount Paid: ₹{amount:.2f}")
    draw_line(f"Reference ID: {reference_id}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer