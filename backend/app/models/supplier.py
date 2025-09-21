from datetime import datetime
from app import db
from app.utils.datetime_type import CustomDateTime

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    
    supplier_id = db.Column(db.String(50), primary_key=True)
    supplier_name_zh = db.Column(db.String(200), nullable=False)
    supplier_name_en = db.Column(db.String(200))
    supplier_address = db.Column(db.Text)
    supplier_phone = db.Column(db.String(50))
    supplier_email = db.Column(db.String(100))
    supplier_contact_person = db.Column(db.String(100))
    supplier_tax_id = db.Column(db.String(20))
    supplier_region = db.Column(db.Enum('domestic', 'international', name='supplier_region_enum'), nullable=False)
    supplier_remark = db.Column(db.Text)
    payment_terms = db.Column(db.String(200))
    bank_account = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(CustomDateTime, default=datetime.utcnow)
    updated_at = db.Column(CustomDateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    purchase_orders = db.relationship('PurchaseOrder', backref='supplier', lazy='dynamic')
    request_order_items = db.relationship('RequestOrderItem', backref='supplier', lazy='dynamic')
    project_expenditures = db.relationship('ProjectSupplierExpenditure', backref='supplier', lazy='dynamic')
    
    def __repr__(self):
        return f'<Supplier {self.supplier_id}: {self.supplier_name_zh}>'
    
    def to_dict(self):
        return {
            'supplier_id': self.supplier_id,
            'supplier_name_zh': self.supplier_name_zh,
            'supplier_name_en': self.supplier_name_en,
            'supplier_address': self.supplier_address,
            'supplier_phone': self.supplier_phone,
            'supplier_email': self.supplier_email,
            'supplier_contact_person': self.supplier_contact_person,
            'supplier_tax_id': self.supplier_tax_id,
            'supplier_region': self.supplier_region,
            'supplier_remark': self.supplier_remark,
            'payment_terms': self.payment_terms,
            'bank_account': self.bank_account,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_summary_dict(self):
        """Lightweight summary for dropdowns and lists"""
        return {
            'supplier_id': self.supplier_id,
            'supplier_name_zh': self.supplier_name_zh,
            'supplier_name_en': self.supplier_name_en,
            'supplier_region': self.supplier_region,
            'payment_terms': self.payment_terms
        }