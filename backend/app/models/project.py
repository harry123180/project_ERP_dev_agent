from datetime import datetime, date
from app import db
from decimal import Decimal

class Project(db.Model):
    __tablename__ = 'projects'
    
    project_id = db.Column(db.String(50), primary_key=True)
    project_code = db.Column(db.String(20))
    project_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    project_status = db.Column(db.Enum('ongoing', 'completed', name='project_status_enum'), default='ongoing')
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    budget = db.Column(db.Numeric(15, 2), default=0)
    total_expenditure = db.Column(db.Numeric(15, 2), default=0)
    customer_name = db.Column(db.String(200))
    customer_contact = db.Column(db.String(100))
    customer_address = db.Column(db.Text)
    customer_phone = db.Column(db.String(50))
    customer_department = db.Column(db.String(100))
    manager_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    manager = db.relationship('User', backref='managed_projects', lazy='select')
    supplier_expenditures = db.relationship('ProjectSupplierExpenditure', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Project {self.project_id}: {self.project_name}>'
    
    def calculate_total_expenditure(self):
        """Calculate and update total expenditure from all suppliers"""
        total = db.session.query(
            db.func.sum(ProjectSupplierExpenditure.expenditure_amount)
        ).filter(
            ProjectSupplierExpenditure.project_id == self.project_id
        ).scalar()
        
        self.total_expenditure = total or Decimal('0')
        return self.total_expenditure
    
    def add_expenditure(self, supplier_id, amount):
        """Add or update expenditure for a supplier"""
        existing = ProjectSupplierExpenditure.query.filter_by(
            project_id=self.project_id,
            supplier_id=supplier_id
        ).first()
        
        if existing:
            existing.expenditure_amount += Decimal(str(amount))
        else:
            expenditure = ProjectSupplierExpenditure(
                project_id=self.project_id,
                supplier_id=supplier_id,
                expenditure_amount=Decimal(str(amount))
            )
            db.session.add(expenditure)
        
        # Recalculate total
        self.calculate_total_expenditure()
    
    def get_supplier_breakdown(self):
        """Get expenditure breakdown by supplier"""
        return [exp.to_dict() for exp in self.supplier_expenditures.all()]
    
    def to_dict(self):
        return {
            'project_id': self.project_id,
            'project_code': self.project_code,
            'project_name': self.project_name,
            'description': self.description,
            'project_status': self.project_status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'budget': float(self.budget) if self.budget else 0,
            'total_expenditure': float(self.total_expenditure),
            'budget_remaining': float(self.budget - self.total_expenditure) if self.budget else None,
            'budget_usage_percent': float((self.total_expenditure / self.budget) * 100) if self.budget and self.budget > 0 else 0,
            'customer_name': self.customer_name,
            'customer_contact': self.customer_contact,
            'customer_address': self.customer_address,
            'customer_phone': self.customer_phone,
            'customer_department': self.customer_department,
            'manager_id': self.manager_id,
            'manager': {
                'user_id': self.manager.user_id,
                'chinese_name': self.manager.chinese_name,
                'username': self.manager.username,
                'department': self.manager.department
            } if self.manager else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'supplier_breakdown': self.get_supplier_breakdown()
        }

class ProjectSupplierExpenditure(db.Model):
    __tablename__ = 'project_supplier_expenditures'
    
    record_id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(50), db.ForeignKey('projects.project_id'), nullable=False)
    supplier_id = db.Column(db.String(50), db.ForeignKey('suppliers.supplier_id'), nullable=False)
    expenditure_amount = db.Column(db.Numeric(15, 2), nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Ensure unique project-supplier combination
    __table_args__ = (db.UniqueConstraint('project_id', 'supplier_id'),)
    
    def __repr__(self):
        return f'<ProjectSupplierExpenditure {self.project_id} - {self.supplier_id}: {self.expenditure_amount}>'
    
    def to_dict(self):
        return {
            'record_id': self.record_id,
            'project_id': self.project_id,
            'supplier_id': self.supplier_id,
            'expenditure_amount': float(self.expenditure_amount),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'supplier': self.supplier.to_summary_dict() if self.supplier else None
        }