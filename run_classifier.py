"""
Esegui con:  python run_classifier.py
Argomenti extra passati direttamente a train.py, es:
  python run_classifier.py --low 1.2 --high 2.8
"""
import subprocess
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

def run(cmd, label):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print(f"\n[ERRORE] {label} fallito (exit {result.returncode}). Interruzione.")
        sys.exit(result.returncode)

extra = sys.argv[1:]  # argomenti aggiuntivi per train.py

run([sys.executable, "classifier/train.py"]    + extra, "1/3  TRAINING")
run([sys.executable, "classifier/classify.py"],          "2/3  CLASSIFICAZIONE")
run([sys.executable, "classifier/plot_classified.py"],   "3/3  PLOT")

print("\n  Tutto completato.")
