from datetime import datetime
from app import db
from werkzeug.security import check_password_hash, generate_password_hash
from app.utils.datetime_type import CustomDateTime

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    chinese_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(100))
    job_title = db.Column(db.String(100))
    role = db.Column(db.String(50), nullable=False, default='Everyone')
    created_at = db.Column(CustomDateTime, default=datetime.utcnow)
    updated_at = db.Column(CustomDateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    created_requisitions = db.relationship('RequestOrder', backref='requester', lazy='dynamic')
    created_purchase_orders = db.relationship('PurchaseOrder', foreign_keys='PurchaseOrder.creator_id', backref='creator', lazy='dynamic')
    outputted_purchase_orders = db.relationship('PurchaseOrder', foreign_keys='PurchaseOrder.output_person_id', backref='output_person', lazy='dynamic')
    confirmed_purchase_orders = db.relationship('PurchaseOrder', foreign_keys='PurchaseOrder.confirm_purchaser_id', backref='confirm_purchaser', lazy='dynamic')
    logistics_events = db.relationship('LogisticsEvent', backref='created_by_user', lazy='dynamic')
    storage_operations = db.relationship('StorageHistory', backref='operator', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def has_role(self, *roles):
        """Check if user has any of the specified roles"""
        if self.role == 'Admin':
            return True  # Admin has all permissions
        return self.role in roles
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'chinese_name': self.chinese_name,
            'username': self.username,
            'department': self.department,
            'job_title': self.job_title,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }