#!/usr/bin/env python3
"""
驗證採購單列表按鈕邏輯
確認狀態與操作按鈕的對應關係符合需求：
- "已建立" (order_created)：編輯 ✓ 輸出 ✓
- "已製單" (outputted)：編輯 ✗ 輸出 ✓
"""

def validate_button_logic():
    """驗證按鈕邏輯函數"""
    
    # 模擬前端的邏輯函數
    def canEdit(purchase_status):
        return purchase_status in ['order_created']
    
    def canOutput(purchase_status):
        return purchase_status in ['order_created', 'outputted']
    
    # 測試案例
    test_cases = [
        {
            'status': 'order_created',
            'chinese_name': '已建立',
            'expected_edit': True,
            'expected_output': True
        },
        {
            'status': 'outputted', 
            'chinese_name': '已製單',
            'expected_edit': False,
            'expected_output': True
        },
        {
            'status': 'pending',
            'chinese_name': '待確認',
            'expected_edit': False,
            'expected_output': False
        },
        {
            'status': 'confirmed',
            'chinese_name': '已確認',
            'expected_edit': False,
            'expected_output': False
        }
    ]
    
    print("🔍 採購單列表按鈕邏輯驗證")
    print("=" * 50)
    
    all_passed = True
    
    for test_case in test_cases:
        status = test_case['status']
        chinese_name = test_case['chinese_name']
        expected_edit = test_case['expected_edit']
        expected_output = test_case['expected_output']
        
        actual_edit = canEdit(status)
        actual_output = canOutput(status)
        
        edit_result = "✓" if actual_edit == expected_edit else "✗"
        output_result = "✓" if actual_output == expected_output else "✗"
        
        if actual_edit != expected_edit or actual_output != expected_output:
            all_passed = False
            
        print(f"狀態: {chinese_name} ({status})")
        print(f"  編輯按鈕: 期望 {expected_edit}, 實際 {actual_edit} {edit_result}")
        print(f"  輸出按鈕: 期望 {expected_output}, 實際 {actual_output} {output_result}")
        print()
    
    print("=" * 50)
    if all_passed:
        print("✅ 所有測試通過！按鈕邏輯符合需求")
    else:
        print("❌ 有測試失敗！按鈕邏輯需要調整")
    
    print("\n📋 需求摘要:")
    print("- '已建立' (order_created): 編輯 ✓ 輸出 ✓")
    print("- '已製單' (outputted): 編輯 ✗ 輸出 ✓") 
    print("- 其他狀態: 編輯 ✗ 輸出 ✗")
    
    return all_passed

if __name__ == "__main__":
    validate_button_logic()