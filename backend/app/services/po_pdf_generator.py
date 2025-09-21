"""
Purchase Order PDF Generator
For now, returns HTML that can be printed to PDF from browser
"""
from .po_html_generator import POHTMLGenerator


class POPDFGenerator:
    """Purchase Order PDF Generator"""
    
    def __init__(self):
        self.html_generator = POHTMLGenerator()
    
    def generate_pdf(self, purchase_order) -> str:
        """Generate PDF-printable HTML from purchase order"""
        # For now, return HTML that can be printed to PDF
        # Users can use Ctrl+P in browser to save as PDF
        return self.html_generator.generate_html(purchase_order)