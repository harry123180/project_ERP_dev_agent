"""
Purchase Order HTML Generator
生成採購單HTML格式，可以直接在瀏覽器中查看並列印
"""
from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal
import base64
import os


class POHTMLGenerator:
    """Purchase Order HTML Generator"""
    
    def get_logo_base64(self):
        """Get TSIC logo as base64 string"""
        # Try multiple possible locations for the logo
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', '..', '..', 'docs', 'TSIC_LOGO.png'),
            os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'docs', 'TSIC_LOGO.png')),
            'docs/TSIC_LOGO.png'
        ]
        
        for logo_path in possible_paths:
            try:
                if os.path.exists(logo_path):
                    with open(logo_path, 'rb') as f:
                        return base64.b64encode(f.read()).decode('utf-8')
            except Exception as e:
                print(f"Error reading logo from {logo_path}: {e}")
        return None
    
    def generate_html(self, purchase_order) -> str:
        """Generate HTML for purchase order"""
        # Add console log to verify this method is called
        print(f"[PDF_GEN] Generating HTML for {purchase_order.purchase_order_no} at {datetime.now().strftime('%H:%M:%S')}")
        print(f"[PDF_GEN] Current margins: 15mm left, 20mm right - BALANCED VERSION v2")

        # Get items
        items = purchase_order.items.all()
        item_count = len(items)
        
        # Build items HTML
        items_html = ""
        for idx, item in enumerate(items, 1):
            items_html += f"""
            <tr>
                <td class="text-center">{idx}</td>
                <td>{item.item_name or ''}</td>
                <td>{item.item_specification or '-'}</td>
                <td>{item.item_model or '-'}</td>
                <td class="text-right">{float(item.item_quantity):.0f}</td>
                <td class="text-center">{item.item_unit or ''}</td>
                <td class="text-right">${float(item.unit_price):,.0f}</td>
                <td class="text-right">${item.line_subtotal_int:,}</td>
                <td></td>
            </tr>
            """
        
        # Only add one empty row if there's only one item
        if item_count == 1:
            items_html += """
            <tr class="empty-row">
                <td>&nbsp;</td>
                <td>&nbsp;</td>
                <td>&nbsp;</td>
                <td>&nbsp;</td>
                <td>&nbsp;</td>
                <td>&nbsp;</td>
                <td>&nbsp;</td>
                <td>&nbsp;</td>
                <td>&nbsp;</td>
            </tr>
            """
        
        # Get logo
        logo_base64 = self.get_logo_base64()
        logo_html = ""
        if logo_base64:
            logo_html = f'<img src="data:image/png;base64,{logo_base64}" alt="TSIC" class="logo">'
        else:
            logo_html = '<div class="logo-text">TSIC</div>'
        
        # Generate HTML
        html = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>採購單 - {purchase_order.purchase_order_no}</title>
    <style>
        @media print {{
            body {{
                margin: 0;
                padding: 0;
            }}
            .no-print {{
                display: none;
            }}
            @page {{
                size: A4;
                margin: 15mm 20mm 15mm 15mm;  /* 平衡的邊距：上15mm 右20mm 下15mm 左15mm - 左右對稱 */
            }}
            .terms-section {{
                page-break-inside: avoid;
            }}
            .signature-section {{
                page-break-inside: avoid;
            }}
        }}
        
        body {{
            font-family: "Microsoft YaHei", "微軟正黑體", "SimSun", "宋體", Arial, sans-serif;
            font-size: 14px;
            line-height: 1.6;
            color: #333;
            max-width: 175mm;  /* A4紙寬210mm減去左右邊距35mm = 175mm可用寬度 */
            margin: 0 auto;  /* 水平置中 */
            padding: 0;  /* 移除額外padding避免偏移 */
            background: white;
        }}
        
        .header {{
            position: relative;
            margin-bottom: 20px;
            min-height: 120px;
        }}
        
        .logo {{
            position: absolute;
            top: 0;
            left: 0;
            width: 270px;
            height: auto;
        }}
        
        .logo-text {{
            position: absolute;
            top: 0;
            left: 0;
            font-size: 86px;
            font-weight: bold;
            color: #0066cc;
        }}
        
        .title-section {{
            text-align: center;
            padding-top: 10px;
            margin-bottom: 20px;
        }}
        
        .title-chinese {{
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .title-english {{
            font-size: 18px;
            color: #666;
            margin-bottom: 10px;
        }}
        
        .title-divider {{
            border-bottom: 2px solid #333;
            margin-top: 15px;
        }}
        
        /* Status badge removed */
        
        .info-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
        }}
        
        .info-table td {{
            padding: 8px;
            border: 1px solid #ddd;
        }}
        
        .info-table .label {{
            background: #f5f5f5;
            font-weight: bold;
            width: 15%;
        }}
        
        .info-table .value {{
            width: 35%;
        }}
        
        .items-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
            margin-top: 15px;
        }}
        
        .items-table th {{
            background: #f0f0f0;
            padding: 8px;
            border: 1px solid #999;
            font-weight: bold;
            text-align: center;
            font-size: 13px;
        }}
        
        .items-table td {{
            padding: 6px;
            border: 1px solid #999;
            font-size: 13px;
        }}
        
        .empty-row td {{
            height: 20px;
            padding: 4px !important;
        }}
        
        .text-center {{
            text-align: center;
        }}
        
        .text-right {{
            text-align: right;
        }}
        
        .summary-section {{
            margin-top: 20px;
            width: 100%;
            border: 1px solid #999;
            border-collapse: collapse;
            page-break-inside: avoid;
        }}
        
        .summary-section td {{
            vertical-align: top;
            padding: 0;
            border: 1px solid #999;
        }}
        
        .terms-cell {{
            padding: 15px;
            background: #f9f9f9;
            width: 60%;
        }}
        
        .terms-list {{
            margin: 0;
            padding-left: 20px;
            font-size: 12px;
            line-height: 1.6;
        }}
        
        .totals-cell {{
            width: 40%;
            padding: 0;
            position: relative;
        }}
        
        .totals-box {{
            border-collapse: collapse;
            width: 100%;
            height: 100%;
            display: table;
        }}
        
        .totals-box td {{
            padding: 10px 15px;
            border-top: 1px solid #999;
            font-size: 13px;
        }}
        
        .totals-box tr:first-child td {{
            border-top: none;
        }}
        
        .totals-box .label {{
            background: #f5f5f5;
            font-weight: bold;
            text-align: right;
            width: 45%;
        }}
        
        .totals-box .value {{
            text-align: right;
            width: 55%;
            background: white;
        }}
        
        .total-row {{
            height: 100%;
        }}
        
        .total-row td {{
            font-size: 14px;
            font-weight: bold;
            background: #e8f4f8 !important;
            color: #0066cc;
            vertical-align: middle !important;
            padding: 15px !important;
        }}
        
        .signature-section {{
            margin-top: 30px;
            page-break-inside: avoid;
        }}
        
        .signature-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .signature-table td {{
            padding: 8px 5px;
            vertical-align: bottom;
        }}
        
        .signature-label {{
            font-weight: bold;
            white-space: nowrap;
        }}
        
        .signature-line {{
            border-bottom: 1px solid #333;
            min-width: 120px;
            display: inline-block;
        }}
        
        .print-button {{
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            z-index: 1000;
        }}
        
        .print-button:hover {{
            background: #0056b3;
        }}
    </style>
</head>
<body>
    <button class="print-button no-print" onclick="window.print()">列印採購單</button>
    
    <div class="header">
        {logo_html}
        <div class="title-section">
            <div class="title-chinese">採購單</div>
            <div class="title-english">PURCHASE ORDER</div>
            <div class="title-divider"></div>
        </div>
    </div>
    
    <table class="info-table">
        <tr>
            <td class="label">廠商名稱</td>
            <td class="value">{purchase_order.supplier_name or ''}</td>
            <td class="label">採購單號</td>
            <td class="value">{purchase_order.purchase_order_no}</td>
        </tr>
        <tr>
            <td class="label">廠商編號</td>
            <td class="value">{purchase_order.supplier_id or ''}</td>
            <td class="label">訂購日期</td>
            <td class="value">{purchase_order.order_date.strftime('%Y/%m/%d') if purchase_order.order_date else ''}</td>
        </tr>
        <tr>
            <td class="label">廠商地址</td>
            <td class="value">{purchase_order.supplier_address or '-'}</td>
            <td class="label">報價單號</td>
            <td class="value">{purchase_order.quotation_no or '-'}</td>
        </tr>
        <tr>
            <td class="label">連絡電話</td>
            <td class="value">{purchase_order.contact_phone or '-'}</td>
            <td class="label">聯絡人</td>
            <td class="value">{purchase_order.contact_person or '-'}</td>
        </tr>
    </table>
    
    <table class="items-table">
        <thead>
            <tr>
                <th width="5%">項次</th>
                <th width="20%">品名</th>
                <th width="15%">規格</th>
                <th width="12%">型號</th>
                <th width="8%">數量</th>
                <th width="8%">單位</th>
                <th width="12%">單價</th>
                <th width="12%">小計</th>
                <th width="8%">備註</th>
            </tr>
        </thead>
        <tbody>
            {items_html}
        </tbody>
    </table>
    
    <table class="summary-section">
        <tr style="height: 40px;">
            <td style="background: #f0f0f0; padding: 8px; font-weight: bold; font-size: 14px; border-bottom: 1px solid #999; border-right: 1px solid #999; width: 60%; vertical-align: middle;">
                注意事項 Terms and Conditions
            </td>
            <td style="border-bottom: 1px solid #999; padding: 0; vertical-align: middle;">
                <table style="width: 100%; border-collapse: collapse; height: 100%;">
                    <tr style="height: 40px;">
                        <td style="background: #f5f5f5; font-weight: bold; text-align: right; width: 45%; padding: 8px 15px; font-size: 13px; vertical-align: middle;">小計 Subtotal</td>
                        <td style="text-align: right; width: 55%; padding: 8px 15px; font-size: 13px; vertical-align: middle;">NT$ {purchase_order.subtotal_int:,}</td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr>
            <td class="terms-cell" rowspan="2">
                <ol class="terms-list">
                    <li>付款條件：月結 30 天</li>
                    <li>交貨期限：訂單確認後 14 個工作天</li>
                    <li>品質要求：須符合國家標準規範</li>
                    <li>驗收標準：貨到 7 日內完成驗收</li>
                    <li>保固期限：自驗收合格日起算一年</li>
                </ol>
            </td>
            <td style="border-bottom: 1px solid #999; padding: 0;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="background: #f5f5f5; font-weight: bold; text-align: right; width: 45%; padding: 10px 15px; font-size: 13px;">稅額 Tax (5%)</td>
                        <td style="text-align: right; width: 55%; padding: 10px 15px; font-size: 13px;">NT$ {float(purchase_order.tax_decimal1):,.1f}</td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr>
            <td style="padding: 0;">
                <table style="width: 100%; border-collapse: collapse; height: 100%;">
                    <tr style="height: 100%;">
                        <td style="background: #e8f4f8; color: #0066cc; font-weight: bold; text-align: right; width: 45%; padding: 15px; font-size: 14px; vertical-align: middle;">總計 Total</td>
                        <td style="background: #e8f4f8; color: #0066cc; font-weight: bold; text-align: right; width: 55%; padding: 15px; font-size: 14px; vertical-align: middle;">NT$ {purchase_order.grand_total_int:,}</td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    
    <div class="signature-section">
        <table class="signature-table">
            <tr>
                <td class="signature-label">製表人：</td>
                <td><span class="signature-line">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span></td>
                <td class="signature-label" style="padding-left: 15px;">日期：</td>
                <td><span class="signature-line">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span></td>
                <td style="width: 50px;">&nbsp;</td>
                <td class="signature-label">採購主管：</td>
                <td><span class="signature-line">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span></td>
                <td class="signature-label" style="padding-left: 15px;">日期：</td>
                <td><span class="signature-line">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span></td>
            </tr>
        </table>
    </div>
</body>
</html>
"""
        return html