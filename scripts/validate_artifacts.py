# scripts/validate_artifacts.py
# 用法：
#   python scripts/validate_artifacts.py
# 需要套件：
#   pip install jsonschema

import json
import sys
from pathlib import Path

try:
    from jsonschema import validate, Draft202012Validator
except Exception as e:
    print("[ERR] 缺少套件 jsonschema，請先執行：pip install jsonschema")
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]  # 專案根目錄
ART = ROOT / "artifacts"
CON = ROOT / "contracts"

# 映射：artifact -> schema
PAIRS = {
    ART / "PLAN.json":               CON / "plan.schema.json",
    ART / "TEST_PLAN.json":          CON / "testplan.schema.json",
    ART / "RUN_REPORT.json":         CON / "runreport.schema.json",
    ART / "PM_SYNC.json":            CON / "pm_sync.schema.json",
    ART / "FE_SPEC.json":            CON / "fe_spec.schema.json",
    ART / "BE_SPEC.json":            CON / "be_spec.schema.json",
    ART / "PURCHASE_FEEDBACK.json":  CON / "purchase_feedback.schema.json",
}

def load_json(p: Path):
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def validate_one(data_path: Path, schema_path: Path):
    # 讀 schema 並檢查合法
    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    # 讀資料並驗證
    instance = load_json(data_path)
    validate(instance=instance, schema=schema)

def main():
    missing = []
    failed = []
    ok = []

    # 先檢查 schema 檔是否都存在
    for schema_path in PAIRS.values():
        if not schema_path.exists():
            print(f"[ERR] 找不到 schema：{schema_path}")
            failed.append(str(schema_path))

    # 逐一驗證存在的 artifacts
    for data_path, schema_path in PAIRS.items():
        if not data_path.exists():
            print(f"[WARN] 略過：{data_path}（檔案不存在）")
            missing.append(str(data_path))
            continue
        try:
            validate_one(data_path, schema_path)
            print(f"[OK]   {data_path}  PASS")
            ok.append(str(data_path))
        except Exception as e:
            print(f"[ERR]  {data_path}  FAIL -> {e}")
            failed.append(str(data_path))

    print("\n=== 驗證結果 ===")
    print(f"通過：{len(ok)} ；失敗：{len(failed)} ；缺檔：{len(missing)}")

    # 若任一失敗，回傳 1（給 GitHub Actions 擋 PR 用）
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
