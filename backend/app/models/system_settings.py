from datetime import datetime
from app import db
from decimal import Decimal

class SystemSettings(db.Model):
    __tablename__ = 'system_settings'
    
    setting_id = db.Column(db.Integer, primary_key=True)
    setting_type = db.Column(db.String(50), nullable=False)
    setting_key = db.Column(db.String(100), nullable=False)
    setting_value = db.Column(db.Text, nullable=False)
    setting_description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Ensure unique type-key combination
    __table_args__ = (db.UniqueConstraint('setting_type', 'setting_key'),)
    
    def __repr__(self):
        return f'<SystemSettings {self.setting_type}.{self.setting_key}: {self.setting_value}>'
    
    @staticmethod
    def get_setting(setting_type, setting_key, default=None):
        """Get a system setting value"""
        setting = SystemSettings.query.filter_by(
            setting_type=setting_type,
            setting_key=setting_key
        ).first()
        
        return setting.setting_value if setting else default
    
    @staticmethod
    def get_decimal_setting(setting_type, setting_key, default=None):
        """Get a system setting as decimal"""
        value = SystemSettings.get_setting(setting_type, setting_key, default)
        try:
            return Decimal(str(value)) if value is not None else None
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def get_float_setting(setting_type, setting_key, default=None):
        """Get a system setting as float"""
        value = SystemSettings.get_setting(setting_type, setting_key, default)
        try:
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def get_int_setting(setting_type, setting_key, default=None):
        """Get a system setting as integer"""
        value = SystemSettings.get_setting(setting_type, setting_key, default)
        try:
            return int(value) if value is not None else default
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def get_bool_setting(setting_type, setting_key, default=False):
        """Get a system setting as boolean"""
        value = SystemSettings.get_setting(setting_type, setting_key, str(default))
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)
    
    @staticmethod
    def set_setting(setting_type, setting_key, setting_value, description=None):
        """Set a system setting value"""
        setting = SystemSettings.query.filter_by(
            setting_type=setting_type,
            setting_key=setting_key
        ).first()
        
        if setting:
            setting.setting_value = str(setting_value)
            if description:
                setting.setting_description = description
        else:
            setting = SystemSettings(
                setting_type=setting_type,
                setting_key=setting_key,
                setting_value=str(setting_value),
                setting_description=description
            )
            db.session.add(setting)
        
        return setting
    
    @staticmethod
    def get_tax_rate():
        """Get default tax rate"""
        return SystemSettings.get_float_setting('tax', 'default_tax_rate', 5.0)
    
    @staticmethod
    def get_company_name():
        """Get company name"""
        return SystemSettings.get_setting('system', 'company_name', 'ERP Company')
    
    @staticmethod
    def get_company_settings():
        """Get all company-related settings"""
        settings = SystemSettings.query.filter_by(setting_type='system').all()
        return {s.setting_key: s.setting_value for s in settings}
    
    @staticmethod
    def get_all_settings_by_type(setting_type):
        """Get all settings of a specific type"""
        settings = SystemSettings.query.filter_by(setting_type=setting_type).all()
        return {s.setting_key: s.setting_value for s in settings}
    
    def to_dict(self):
        return {
            'setting_id': self.setting_id,
            'setting_type': self.setting_type,
            'setting_key': self.setting_key,
            'setting_value': self.setting_value,
            'setting_description': self.setting_description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }