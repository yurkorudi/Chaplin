"""One print-ready A5 page per paid seat, with an opaque verification QR."""
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

def build_pdf(order):
    if order.status!='paid':
        raise ValueError('Only paid orders have tickets.')
    root=Path(__file__).resolve().parent
    for font,file in [('Chaplin','DejaVuSans.ttf'),('ChaplinBold','DejaVuSans-Bold.ttf')]:
        if font not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(font,str(root/'static/fonts'/file)))
    output=BytesIO();pdf=canvas.Canvas(output,pagesize=A5)
    width,height=A5
    style=ParagraphStyle('film',fontName='ChaplinBold',fontSize=18,leading=24,textColor=colors.HexColor('#811a26'))
    for ticket in order.tickets:
        show=ticket.session
        pdf.setFillColor(colors.HexColor('#811a26'));pdf.rect(0,height-88,width,88,fill=1,stroke=0)
        pdf.setFillColor(colors.white);pdf.setFont('ChaplinBold',28);pdf.drawString(28,height-43,'Chaplin')
        pdf.setFont('Chaplin',10);pdf.drawString(29,height-64,'CINEMA  /  ЕЛЕКТРОННИЙ КВИТОК')
        title=Paragraph(escape(show.film.name),style);_,h=title.wrap(width-56,100);title.drawOn(pdf,28,height-112-h)
        y=height-140-h
        pdf.setFillColor(colors.HexColor('#222222'))
        lines=[show.session_datetime.strftime('%d.%m.%Y  •  %H:%M'),show.cinema.name,show.cinema.location,f'{show.hall.name}  /  Ряд {ticket.row_index+1}  /  Місце {ticket.column_index+1}',f'Квиток № {ticket.ticket_id}',f'Сума: {ticket.cost:.2f} UAH  /  СПЛАЧЕНО']
        for line in lines:
            paragraph=Paragraph(escape(line),ParagraphStyle('line',fontName='Chaplin',fontSize=11,leading=16))
            _,lh=paragraph.wrap(width-56,50);paragraph.drawOn(pdf,28,y-lh);y-=lh+9
        qr=QrCodeWidget(ticket.token);bounds=qr.getBounds();size=105
        drawing=Drawing(size,size,transform=[size/(bounds[2]-bounds[0]),0,0,size/(bounds[3]-bounds[1]),0,0]);drawing.add(qr)
        renderPDF.draw(drawing,pdf,width-140,55)
        pdf.setFont('Chaplin',8);pdf.drawString(28,45,f'Замовлення: {order.id}')
        pdf.setFont('Chaplin',8);pdf.drawString(28,30,'ДЕМО-ПРОДАЖ. Не є фіскальним чеком.' if order.is_demo else 'Збережіть квиток до завершення сеансу.')
        pdf.showPage()
    pdf.save();output.seek(0);return output
