import os
from app import create_app, db
from app.models import User, Supplier, RequestOrder, PurchaseOrder, Storage
from app.websocket import socketio

# Create Flask application
app = create_app(os.getenv('FLASK_ENV'))

# Shell context for Flask CLI
@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Supplier': Supplier,
        'RequestOrder': RequestOrder,
        'PurchaseOrder': PurchaseOrder,
        'Storage': Storage
    }

# Create database tables
@app.cli.command()
def init_db():
    """Create database tables."""
    db.create_all()
    print('Database initialized!')

# Create sample data
@app.cli.command()
def seed_db():
    """Create sample data."""
    from app.models import User, Supplier, ItemCategory, SystemSettings
    from werkzeug.security import generate_password_hash
    
    # Create admin user
    admin = User(
        chinese_name='系統管理員',
        username='admin',
        password=generate_password_hash('admin123'),
        department='IT',
        role='Admin'
    )
    
    # Create test users
    procurement = User(
        chinese_name='採購專員',
        username='procurement',
        password=generate_password_hash('proc123'),
        department='採購部',
        role='Procurement'
    )
    
    engineer = User(
        chinese_name='工程師',
        username='engineer',
        password=generate_password_hash('eng123'),
        department='工程部',
        role='Everyone'
    )
    
    # Create sample suppliers
    supplier1 = Supplier(
        supplier_id='T001',
        supplier_name_zh='台積電',
        supplier_name_en='TSMC',
        supplier_region='domestic',
        supplier_phone='02-12345678',
        supplier_email='contact@tsmc.com',
        payment_terms='月結30天'
    )
    
    supplier2 = Supplier(
        supplier_id='I001',
        supplier_name_zh='英特爾',
        supplier_name_en='Intel Corporation',
        supplier_region='international',
        supplier_phone='+1-408-765-8080',
        supplier_email='contact@intel.com',
        payment_terms='月結60天'
    )
    
    # Create item categories
    categories = [
        ItemCategory(category_code='01', category_name='電子元件', sort_order=1),
        ItemCategory(category_code='02', category_name='機械零件', sort_order=2),
        ItemCategory(category_code='03', category_name='辦公用品', sort_order=3),
        ItemCategory(category_code='04', category_name='實驗設備', sort_order=4),
    ]
    
    # Create system settings
    settings = [
        SystemSettings(
            setting_type='tax',
            setting_key='default_tax_rate',
            setting_value='5.0',
            setting_description='預設稅率(%)'
        ),
        SystemSettings(
            setting_type='system',
            setting_key='company_name',
            setting_value='創新科技股份有限公司',
            setting_description='公司名稱'
        ),
    ]
    
    # Add all to database
    db.session.add_all([admin, procurement, engineer, supplier1, supplier2] + categories + settings)
    db.session.commit()
    print('Sample data created!')

if __name__ == '__main__':
    # Use SocketIO.run instead of app.run for WebSocket support
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, use_reloader=True)