#!/usr/bin/env python
"""
Create test supplier data
"""

from app import create_app, db
from app.models.supplier import Supplier
from datetime import datetime

def create_test_suppliers():
    """Create test supplier data"""
    app = create_app()
    
    with app.app_context():
        try:
            # Test suppliers data
            suppliers = [
                {
                    'supplier_id': 'S001',
                    'supplier_name_zh': '台積電科技有限公司',
                    'supplier_name_en': 'TSMC Technology Co., Ltd.',
                    'supplier_address': '新竹科學園區創新一路25號',
                    'supplier_phone': '03-5678900',
                    'supplier_email': 'contact@tsmc-tech.com',
                    'supplier_contact_person': '王經理',
                    'supplier_tax_id': '53012345',
                    'supplier_region': 'domestic',
                    'payment_terms': '月結30天',
                    'bank_account': '0123456789012345',
                    'supplier_remark': '主要半導體供應商',
                    'is_active': True
                },
                {
                    'supplier_id': 'S002',
                    'supplier_name_zh': '鴻海精密工業',
                    'supplier_name_en': 'Foxconn Technology',
                    'supplier_address': '土城工業區自強路1號',
                    'supplier_phone': '02-22689999',
                    'supplier_email': 'supplier@foxconn.com',
                    'supplier_contact_person': '李副理',
                    'supplier_tax_id': '04541302',
                    'supplier_region': 'domestic',
                    'payment_terms': '月結60天',
                    'bank_account': '9876543210987654',
                    'supplier_remark': '電子零件供應商',
                    'is_active': True
                },
                {
                    'supplier_id': 'S003',
                    'supplier_name_zh': '英特爾科技',
                    'supplier_name_en': 'Intel Technology',
                    'supplier_address': '2200 Mission College Blvd, Santa Clara, CA',
                    'supplier_phone': '+1-408-765-8080',
                    'supplier_email': 'supplier@intel.com',
                    'supplier_contact_person': 'John Smith',
                    'supplier_tax_id': 'US942540110',
                    'supplier_region': 'international',
                    'payment_terms': 'T/T 30 days',
                    'bank_account': 'SWIFT: CHASUS33',
                    'supplier_remark': '處理器供應商',
                    'is_active': True
                },
                {
                    'supplier_id': 'S004',
                    'supplier_name_zh': '華碩電腦',
                    'supplier_name_en': 'ASUS Computer',
                    'supplier_address': '北投區立德路15號',
                    'supplier_phone': '02-28943447',
                    'supplier_email': 'business@asus.com',
                    'supplier_contact_person': '陳經理',
                    'supplier_tax_id': '23638777',
                    'supplier_region': 'domestic',
                    'payment_terms': '月結45天',
                    'bank_account': '1234567890123456',
                    'supplier_remark': '電腦設備供應商',
                    'is_active': True
                },
                {
                    'supplier_id': 'S005',
                    'supplier_name_zh': '三星電子',
                    'supplier_name_en': 'Samsung Electronics',
                    'supplier_address': 'Samsung-ro, Yeongtong-gu, Suwon-si, Korea',
                    'supplier_phone': '+82-31-200-1114',
                    'supplier_email': 'supplier@samsung.com',
                    'supplier_contact_person': 'Kim Lee',
                    'supplier_tax_id': 'KR1248100998',
                    'supplier_region': 'international',
                    'payment_terms': 'L/C 60 days',
                    'bank_account': 'SWIFT: KOEXKRSE',
                    'supplier_remark': '記憶體與顯示器供應商',
                    'is_active': True
                },
                {
                    'supplier_id': 'S006',
                    'supplier_name_zh': '宏達電子',
                    'supplier_name_en': 'HTC Corporation',
                    'supplier_address': '桃園市龜山區興業路5號',
                    'supplier_phone': '03-3753252',
                    'supplier_email': 'business@htc.com',
                    'supplier_contact_person': '張協理',
                    'supplier_tax_id': '16003518',
                    'supplier_region': 'domestic',
                    'payment_terms': '月結30天',
                    'bank_account': '5555666677778888',
                    'supplier_remark': '行動裝置供應商',
                    'is_active': False  # Inactive supplier for testing
                }
            ]
            
            # Create suppliers
            created_count = 0
            updated_count = 0
            
            for supplier_data in suppliers:
                existing = Supplier.query.get(supplier_data['supplier_id'])
                
                if existing:
                    # Update existing supplier
                    for key, value in supplier_data.items():
                        setattr(existing, key, value)
                    updated_count += 1
                    print(f"Updated supplier: {supplier_data['supplier_id']} - {supplier_data['supplier_name_zh']}")
                else:
                    # Create new supplier
                    supplier = Supplier(**supplier_data)
                    db.session.add(supplier)
                    created_count += 1
                    print(f"Created supplier: {supplier_data['supplier_id']} - {supplier_data['supplier_name_zh']}")
            
            db.session.commit()
            
            print(f"\n✅ Supplier test data created successfully!")
            print(f"   Created: {created_count} suppliers")
            print(f"   Updated: {updated_count} suppliers")
            
            # Display summary
            total_suppliers = Supplier.query.count()
            active_suppliers = Supplier.query.filter_by(is_active=True).count()
            domestic_suppliers = Supplier.query.filter_by(supplier_region='domestic').count()
            international_suppliers = Supplier.query.filter_by(supplier_region='international').count()
            
            print(f"\n📊 Supplier Summary:")
            print(f"   Total suppliers: {total_suppliers}")
            print(f"   Active suppliers: {active_suppliers}")
            print(f"   Domestic suppliers: {domestic_suppliers}")
            print(f"   International suppliers: {international_suppliers}")
            
        except Exception as e:
            print(f"Error creating supplier test data: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    create_test_suppliers()