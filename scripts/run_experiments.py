import argparse
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from finguia.evaluation import record_environment, run_generation, run_retrieval

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--generation',action='store_true')
    args = parser.parse_args()
    run_retrieval()
    if args.generation:
        run_generation()
    record_environment()
