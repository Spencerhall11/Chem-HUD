# Chem-HUD
A real-time chemical formula analyzer that reads text directly from your screen. Hover your mouse over any chemical formula in a paper or document and ChemHUD identifies it and returns the molecular mass instantly.  Built as a visualization tool for reading chemistry papers without constantly switching to reference tabs.

How it works:
3 languages used for areas of particular note

**C++ (`ScreenReaderEye.cpp`)** — Captures the screen in real time using low-level Windows APIs and performs OCR to extract text from the region around the mouse cursor.

**Python (`Nerve.py`, `predict.py`, `ChemModel.py`)** — A trained ML model identifies chemical formula patterns in the extracted text and pipes valid formula strings to the Haskell brain.

**Haskell (`app/`)** — A recursive descent parser built with Parsec converts formula strings like `Mg(OH)2` into a nested data structure and computes the exact molecular mass from a local periodic table lookup. Runs as a persistent process receiving input via stdin.

architecture:
1. Screen Capture (C++)
2. ML Formula detection (Python)
3. Parser+Mass Calculation (Haskell)
4. Output

The Haskell layer models chemical formulas as a recursive data type — a molecule is a list of components, and each component is either a single atom with a count or a bracketed sub-molecule with a count. This handles arbitrary nesting naturally:

- `H2O` → 2 hydrogen + 1 oxygen
- `Mg(OH)2` → 1 magnesium + 2×(1 oxygen + 1 hydrogen)
- `Ca(NO3)2` → 1 calcium + 2×(1 nitrogen + 3 oxygen)

Atomic masses are loaded from a local CSV of the periodic table into a hash map for O(1) lookup.

Stack:
- C++ — screen capture and OCR
- Python — ML inference (PyTorch), trained on a synthetically generated dataset of ~50,000 images with varied fonts, colors, and chemical formula combinations
- Haskell — formula parsing and mass calculation (Parsec, Cabal)

Running:
```bash
launchHud.bat
```

The batch file starts all three components and connects the pipeline.



Status:
Core is functional with screen capture,formula detection, and molecular mass output all working end to end. The planned atomic structure visualizing was scoped out.
