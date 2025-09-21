"""
Fixed Purchase Order PDF Generation Service
修正中文字體和格式問題
"""
import os
import io
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from decimal import Decimal
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, Image, PageBreak, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Line, Rect
from reportlab.platypus.flowables import HRFlowable

# Import standard fonts that support Chinese
from reportlab.pdfbase.cidfonts import UnicodeCIDFont


class FixedPOGenerator:
    """Fixed Purchase Order PDF Generator with better Chinese support"""
    
    def __init__(self):
        # Register Chinese CID fonts (built-in support)
        try:
            pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
            self.chinese_font = 'STSong-Light'
            print(f"Using CID font: {self.chinese_font}")
        except:
            # Fallback to Helvetica if CID font fails
            self.chinese_font = 'Helvetica'
            print(f"Fallback to: {self.chinese_font}")
    
    def generate_pdf(self, purchase_order) -> bytes:
        """Generate PDF with better formatting"""
        # Create PDF in memory
        buffer = io.BytesIO()
        
        # Create document with custom margins
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm,
            title=f"Purchase Order - {purchase_order.purchase_order_no}",
            author="ERP System"
        )
        
        # Build PDF elements
        elements = self._build_elements(purchase_order)
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF data
        buffer.seek(0)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
    
    def _build_elements(self, po):
        """Build all PDF elements"""
        elements = []
        styles = self._get_custom_styles()
        
        # Title
        elements.append(Paragraph('TSIC', styles['CompanyName']))
        elements.append(Spacer(1, 5*mm))
        
        # Purchase Order Title
        title_data = [
            ['採購單', '', '狀態: 已製單'],
            ['PURCHASE ORDER', '', '']
        ]
        title_table = Table(title_data, colWidths=[60*mm, 80*mm, 40*mm])
        title_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 1), 'LEFT'),
            ('ALIGN', (1, 0), (1, 1), 'CENTER'),
            ('ALIGN', (2, 0), (2, 1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (0, 0), 16),
            ('FONTSIZE', (0, 1), (0, 1), 12),
            ('FONTSIZE', (2, 0), (2, 0), 10),
            ('LINEBELOW', (0, 1), (-1, 1), 1, colors.black),
        ]))
        elements.append(title_table)
        elements.append(Spacer(1, 8*mm))
        
        # Basic info table
        info_data = [
            ['廠商名稱', po.supplier_name or '', '採購單號', po.purchase_order_no],
            ['廠商編號', po.supplier_id or '', '訂購日期', 
             po.order_date.strftime('%Y/%m/%d') if po.order_date else ''],
            ['廠商地址', po.supplier_address or '-', '報價單號', po.quotation_no or '-'],
            ['連絡電話', po.contact_phone or '-', '聯絡人', po.contact_person or '-']
        ]
        
        info_table = Table(
            info_data,
            colWidths=[25*mm, 55*mm, 25*mm, 55*mm]
        )
        
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.95, 0.95, 0.95)),
            ('BACKGROUND', (2, 0), (2, -1), colors.Color(0.95, 0.95, 0.95)),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 8*mm))
        
        # Items section title
        elements.append(Paragraph('採購明細 Purchase Items', styles['SectionTitle']))
        elements.append(Spacer(1, 3*mm))
        
        # Items table
        items_data = [
            ['項次', '品名', '規格', '型號', '數量', '單位', '單價', '小計', '備註']
        ]
        
        items = po.items.all()
        for idx, item in enumerate(items, 1):
            row = [
                str(idx),
                item.item_name or '',
                item.item_specification or '-',
                item.item_model or '-',
                f'{float(item.item_quantity):.0f}',
                item.item_unit or '',
                f'${float(item.unit_price):,.0f}',
                f'${item.line_subtotal_int:,}',
                ''
            ]
            items_data.append(row)
        
        # Add empty rows if less than 5 items
        while len(items_data) < 6:
            items_data.append(['', '', '', '', '', '', '', '', ''])
        
        items_table = Table(
            items_data,
            colWidths=[12*mm, 35*mm, 25*mm, 20*mm, 15*mm, 12*mm, 18*mm, 20*mm, 13*mm]
        )
        
        items_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
            ('FONTNAME', (0, 0), (-1, 0), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # 項次
            ('ALIGN', (4, 1), (4, -1), 'RIGHT'),   # 數量
            ('ALIGN', (5, 1), (5, -1), 'CENTER'),  # 單位
            ('ALIGN', (6, 1), (7, -1), 'RIGHT'),   # 單價, 小計
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        
        elements.append(items_table)
        elements.append(Spacer(1, 5*mm))
        
        # Totals
        totals_data = [
            ['', '', '', '', '', '小計 Subtotal：', f'NT$ {po.subtotal_int:,}'],
            ['', '', '', '', '', '稅額 Tax (5%)：', f'NT$ {float(po.tax_decimal1):,.1f}'],
            ['', '', '', '', '', '總計 Total：', f'NT$ {po.grand_total_int:,}']
        ]
        
        totals_table = Table(
            totals_data,
            colWidths=[25*mm, 35*mm, 25*mm, 20*mm, 28*mm, 22*mm, 25*mm]
        )
        
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, 1), 9),
            ('FONTSIZE', (5, 2), (6, 2), 10),
            ('ALIGN', (5, 0), (5, -1), 'RIGHT'),
            ('ALIGN', (6, 0), (6, -1), 'RIGHT'),
            ('TEXTCOLOR', (5, 2), (6, 2), colors.HexColor('#0066cc')),
            ('LINEABOVE', (5, 2), (6, 2), 1, colors.black),
            ('TOPPADDING', (5, 2), (6, 2), 3),
            ('BOTTOMPADDING', (5, 2), (6, 2), 3),
        ]))
        
        elements.append(totals_table)
        elements.append(Spacer(1, 8*mm))
        
        # Terms
        terms_data = [
            ['注意事項 Terms and Conditions'],
            ['1. 付款條件：月結 30 天'],
            ['2. 交貨期限：訂單確認後 14 個工作天'],
            ['3. 品質要求：須符合國家標準規範'],
            ['4. 驗收標準：貨到 7 日內完成驗收'],
            ['5. 保固期限：自驗收合格日起算一年']
        ]
        
        terms_table = Table(terms_data, colWidths=[170*mm])
        terms_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (0, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.98, 0.98, 0.98)),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(terms_table)
        elements.append(Spacer(1, 10*mm))
        
        # Signature
        sig_data = [
            ['採購人員：', '_____________________', '', '核准主管：', '_____________________'],
            ['', '', '', '', ''],
            ['日期：', '_____________________', '', '日期：', '_____________________']
        ]
        
        sig_table = Table(
            sig_data,
            colWidths=[20*mm, 45*mm, 30*mm, 20*mm, 45*mm]
        )
        
        sig_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ]))
        
        elements.append(sig_table)
        
        return elements
    
    def _get_custom_styles(self):
        """Get custom paragraph styles"""
        styles = getSampleStyleSheet()
        
        # Company name
        styles.add(ParagraphStyle(
            name='CompanyName',
            parent=styles['Title'],
            fontName=self.chinese_font,
            fontSize=24,
            textColor=colors.HexColor('#333333'),
            alignment=TA_LEFT,
            spaceAfter=0
        ))
        
        # Section title
        styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=styles['Heading2'],
            fontName=self.chinese_font,
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            spaceAfter=5
        ))
        
        return styles