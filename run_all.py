import subprocess
import sys

scripts = [
    "update_data.py",
    "scripts/export_returns.py",
    "scripts/export_heatmap.py",
    "scripts/export_global_wave.py",
    "strat.py",
]

#

for script in scripts:
    print(f"\n=== Running {script} ===")
    
    result = subprocess.run([sys.executable, script])
    
    if result.returncode != 0:
        print(f"Error running {script}")
        break

print("\nAll scripts finished.")

##  更新不能按Run的鍵  一定要用指令更新
##  更新要下指令  python run_all.py
