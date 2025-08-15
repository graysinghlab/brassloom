
"""
brassloom_cli.py
- Runs the harvester, then syncs to the GSU workbook.
Usage:
  python brassloom_cli.py --days 60 --gsu /path/to/GSU_Cayuse_Lite.xlsx
"""
import argparse, os, subprocess, sys
HERE = os.path.dirname(__file__)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=60)
    ap.add_argument("--keywords", default="HBCU,MSI,minority serving,HSI,Tribal,TCU,Black,broadening participation,EPSCoR")
    ap.add_argument("--out", default=os.path.join(HERE, "opportunities.json"))
    ap.add_argument("--gsu", default=os.path.join(HERE, "GSU_Cayuse_Lite.xlsx"))
    ap.add_argument("--sync_filter", default="")  # default uses config keywords
    args = ap.parse_args()

    # Harvest
    harvester = os.path.join(HERE, "brassloom_harvest.py")
    cmd = [sys.executable, harvester, "--out", args.out, "--days", str(args.days), "--keywords", args.keywords]
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)

    # Sync
    syncer = os.path.join(HERE, "brassloom_sync_gsu.py")
    cmd2 = [sys.executable, syncer, "--ops", args.out, "--wb", args.gsu]
    if args.sync_filter:
        cmd2 += ["--filter", args.sync_filter]
    else:
        cmd2 += ["--all"]
    print("Running:", " ".join(cmd2))
    subprocess.check_call(cmd2)

if __name__ == "__main__":
    main()
