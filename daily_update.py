import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(r"C:\Users\admin\Desktop\factor-platform")
PYTHON_EXE = sys.executable

def run_cmd(cmd, cwd=PROJECT_DIR, allow_fail=False):
    print(f"\n>>> 執行: {' '.join(map(str, cmd))}")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0 and not allow_fail:
        raise RuntimeError(f"指令失敗，return code = {result.returncode}")
    return result

def main():

    
    # 1. 更新 Excel / CMoney
    run_cmd([PYTHON_EXE, "xlsx_automation.py"])

    # 2. 跑主流程
    run_cmd([PYTHON_EXE, "run_all.py"])

    # 3. Git
    run_cmd(["git", "add", "."])

    commit_result = run_cmd(
        ["git", "commit", "-m", "daily data update"],
        allow_fail=True
    )
    if commit_result.returncode != 0:
        print(">>> 沒有可提交的變更，略過 commit")

    run_cmd(["git", "push"])

    print("\n✅ 全部流程完成")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 流程失敗: {e}")
        sys.exit(1)