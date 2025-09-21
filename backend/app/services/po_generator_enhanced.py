"""
Enhanced Purchase Order PDF Generation Service
Improved layout and styling to match frontend preview
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
    Spacer, Image, PageBreak, KeepTogether, Frame,
    PageTemplate, BaseDocTemplate
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Line, Rect
from reportlab.platypus.flowables import HRFlowable


class EnhancedPOGenerator:
    """Enhanced Purchase Order PDF Generator with better formatting"""
    
    def __init__(self):
        # Try to register Chinese fonts
        self._register_fonts()
        
    def _register_fonts(self):
        """Register Chinese fonts for PDF generation"""
        # Try multiple font options
        font_options = [
            ("C:/Windows/Fonts/msjh.ttc", "MSJhengHei"),  # Microsoft JhengHei
            ("C:/Windows/Fonts/mingliu.ttc", "MingLiU"),  # MingLiU
            ("C:/Windows/Fonts/kaiu.ttf", "DFKai-SB"),    # DFKai-SB
            ("C:/Windows/Fonts/simsun.ttc", "SimSun"),    # SimSun
        ]
        
        self.chinese_font = "Helvetica"  # Default fallback
        self.chinese_bold_font = "Helvetica-Bold"
        
        for font_path, font_name in font_options:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, font_path, subfontIndex=0))
                    pdfmetrics.registerFont(TTFont(f"{font_name}-Bold", font_path, subfontIndex=1))
                    self.chinese_font = font_name
                    self.chinese_bold_font = f"{font_name}-Bold"
                    break
                except:
                    continue
        
        # If no TrueType fonts work, try CID fonts
        if self.chinese_font == "Helvetica":
            try:
                pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
                self.chinese_font = 'STSong-Light'
                self.chinese_bold_font = 'STSong-Light'
            except:
                pass
    
    def generate_pdf(self, purchase_order) -> bytes:
        """Generate enhanced PDF with better layout"""
        # Create PDF in memory
        buffer = io.BytesIO()
        
        # Create document with custom margins
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=20*mm,
            title=f"採購單 - {purchase_order.purchase_order_no}",
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
        
        # Company header with logo placeholder
        elements.append(self._create_header(po, styles))
        elements.append(Spacer(1, 10*mm))
        
        # Basic info table (4x4 grid like frontend)
        elements.append(self._create_info_table(po, styles))
        elements.append(Spacer(1, 8*mm))
        
        # Items table
        elements.append(Paragraph('<b>採購明細 Purchase Items</b>', styles['SectionTitle']))
        elements.append(Spacer(1, 3*mm))
        elements.append(self._create_items_table(po, styles))
        elements.append(Spacer(1, 5*mm))
        
        # Totals
        elements.append(self._create_totals_table(po, styles))
        elements.append(Spacer(1, 8*mm))
        
        # Terms and conditions
        elements.append(self._create_terms_section(po, styles))
        elements.append(Spacer(1, 10*mm))
        
        # Signature area
        elements.append(self._create_signature_section(styles))
        
        return elements
    
    def _get_custom_styles(self):
        """Get custom paragraph styles"""
        styles = getSampleStyleSheet()
        
        # Main title style
        styles.add(ParagraphStyle(
            name='MainTitle',
            parent=styles['Title'],
            fontName=self.chinese_bold_font,
            fontSize=20,
            textColor=colors.HexColor('#333333'),
            alignment=TA_CENTER,
            spaceAfter=0
        ))
        
        # Subtitle style
        styles.add(ParagraphStyle(
            name='SubTitle',
            parent=styles['Normal'],
            fontName=self.chinese_font,
            fontSize=14,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
            spaceAfter=10
        ))
        
        # Section title
        styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=styles['Heading2'],
            fontName=self.chinese_bold_font,
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            borderColor=colors.HexColor('#409eff'),
            borderWidth=1,
            borderPadding=2,
            spaceAfter=5
        ))
        
        # Normal text
        styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=styles['Normal'],
            fontName=self.chinese_font,
            fontSize=9,
            leading=12
        ))
        
        # Small text
        styles.add(ParagraphStyle(
            name='SmallText',
            parent=styles['Normal'],
            fontName=self.chinese_font,
            fontSize=8,
            leading=10
        ))
        
        return styles
    
    def _create_header(self, po, styles):
        """Create company header section"""
        # Header data with three columns
        header_data = []
        
        # Row 1: Logo placeholder | Title | Status
        logo_cell = Paragraph('TSIC', styles['MainTitle'])
        title_cell = [
            Paragraph('<b>採購單</b>', styles['MainTitle']),
            Paragraph('PURCHASE ORDER', styles['SubTitle'])
        ]
        
        status_map = {
            'pending': '待處理',
            'order_created': '已建立',
            'outputted': '已製單',
            'purchased': '已採購',
            'shipped': '已出貨'
        }
        status_text = status_map.get(po.purchase_status, po.purchase_status)
        status_cell = Paragraph(f'<b>狀態: {status_text}</b>', styles['CustomNormal'])
        
        header_table = Table(
            [[logo_cell, title_cell, status_cell]],
            colWidths=[50*mm, 90*mm, 40*mm],
            rowHeights=[15*mm]
        )
        
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#333333')),
        ]))
        
        return header_table
    
    def _create_info_table(self, po, styles):
        """Create 4x4 info table matching frontend layout"""
        info_data = [
            ['廠商名稱', po.supplier_name or '', '採購單號', po.purchase_order_no],
            ['廠商編號', po.supplier_id or '', '訂購日期', 
             po.order_date.strftime('%Y/%m/%d') if po.order_date else ''],
            ['廠商地址', po.supplier_address or '-', '報價單號', po.quotation_no or '-'],
            ['連絡電話', po.contact_phone or '-', '聯絡人', po.contact_person or '-']
        ]
        
        # Convert to paragraph objects for better text handling
        para_data = []
        for row in info_data:
            para_row = []
            for i, cell in enumerate(row):
                if i % 2 == 0:  # Label columns
                    para_row.append(Paragraph(f'<b>{cell}</b>', styles['SmallText']))
                else:  # Value columns
                    para_row.append(Paragraph(str(cell), styles['CustomNormal']))
            para_data.append(para_row)
        
        info_table = Table(
            para_data,
            colWidths=[30*mm, 60*mm, 30*mm, 60*mm],
            rowHeights=[8*mm] * 4
        )
        
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#333333')),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f0f0f0')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        return info_table
    
    def _create_items_table(self, po, styles):
        """Create items table with better formatting"""
        # Table headers
        headers = ['項次', '品名', '規格', '型號', '數量', '單位', '單價', '小計', '備註']
        
        # Prepare data
        items_data = [headers]
        
        items = po.items.all()
        for idx, item in enumerate(items, 1):
            row = [
                str(idx),
                item.item_name or '',
                item.item_specification or '-',
                item.item_model or '-',
                f'{float(item.item_quantity):.0f}',
                item.item_unit or '',
                f'${float(item.unit_price):,.2f}',
                f'${item.line_subtotal_int:,}',
                '-'
            ]
            items_data.append(row)
        
        # Add empty rows if less than 5 items (for better layout)
        while len(items_data) < 6:
            items_data.append(['', '', '', '', '', '', '', '', ''])
        
        # Create table
        items_table = Table(
            items_data,
            colWidths=[15*mm, 35*mm, 30*mm, 25*mm, 15*mm, 12*mm, 20*mm, 22*mm, 15*mm],
            rowHeights=[8*mm] + [7*mm] * (len(items_data) - 1)
        )
        
        # Apply styles
        items_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#000000')),
            ('FONTNAME', (0, 0), (-1, 0), self.chinese_bold_font),
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
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#333333')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        return items_table
    
    def _create_totals_table(self, po, styles):
        """Create totals section"""
        totals_data = [
            ['', '', '', '', '', '小計 Subtotal：', f'NT$ {po.subtotal_int:,}'],
            ['', '', '', '', '', '稅額 Tax (5%)：', f'NT$ {float(po.tax_decimal1):,.1f}'],
            ['', '', '', '', '', '總計 Total：', f'NT$ {po.grand_total_int:,}']
        ]
        
        totals_table = Table(
            totals_data,
            colWidths=[25*mm, 35*mm, 30*mm, 25*mm, 30*mm, 25*mm, 30*mm],
            rowHeights=[6*mm, 6*mm, 8*mm]
        )
        
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, 1), 9),
            ('FONTSIZE', (5, 2), (6, 2), 11),
            ('ALIGN', (5, 0), (5, -1), 'RIGHT'),
            ('ALIGN', (6, 0), (6, -1), 'RIGHT'),
            ('TEXTCOLOR', (5, 2), (6, 2), colors.HexColor('#409eff')),
            ('FONTNAME', (5, 2), (6, 2), self.chinese_bold_font),
            ('LINEABOVE', (5, 2), (6, 2), 1.5, colors.HexColor('#333333')),
            ('BACKGROUND', (5, 2), (6, 2), colors.HexColor('#f0f7ff')),
            ('TOPPADDING', (5, 2), (6, 2), 3),
            ('BOTTOMPADDING', (5, 2), (6, 2), 3),
        ]))
        
        return totals_table
    
    def _create_terms_section(self, po, styles):
        """Create terms and conditions section"""
        terms_text = """
        <b>注意事項 Terms and Conditions</b><br/>
        1. 付款條件：月結 30 天<br/>
        2. 交貨期限：訂單確認後 14 個工作天<br/>
        3. 品質要求：須符合國家標準規範<br/>
        4. 驗收標準：貨到 7 日內完成驗收<br/>
        5. 保固期限：自驗收合格日起算一年
        """
        
        terms_para = Paragraph(terms_text, styles['SmallText'])
        
        # Create a bordered box for terms
        terms_table = Table([[terms_para]], colWidths=[180*mm])
        terms_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        return terms_table
    
    def _create_signature_section(self, styles):
        """Create signature section"""
        sig_data = [
            [Paragraph('採購人員：', styles['CustomNormal']), 
             '_____________________',
             '',
             Paragraph('核准主管：', styles['CustomNormal']),
             '_____________________'],
            ['', '', '', '', ''],
            [Paragraph('日期：', styles['CustomNormal']),
             '_____________________',
             '',
             Paragraph('日期：', styles['CustomNormal']),
             '_____________________']
        ]
        
        sig_table = Table(
            sig_data,
            colWidths=[25*mm, 50*mm, 30*mm, 25*mm, 50*mm],
            rowHeights=[8*mm, 5*mm, 8*mm]
        )
        
        sig_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ]))
        
        return sig_table