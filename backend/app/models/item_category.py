from datetime import datetime
from app import db

class ItemCategory(db.Model):
    __tablename__ = 'item_categories'
    
    category_id = db.Column(db.Integer, primary_key=True)
    category_code = db.Column(db.String(10), unique=True, nullable=False)
    category_name = db.Column(db.String(100), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    request_order_items = db.relationship('RequestOrderItem', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<ItemCategory {self.category_code}: {self.category_name}>'
    
    def to_dict(self):
        return {
            'category_id': self.category_id,
            'category_code': self.category_code,
            'category_name': self.category_name,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }