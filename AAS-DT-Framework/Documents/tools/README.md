# Thesis Figure & Plot Generation Tools

This directory houses all Python automation scripts used to generate publication-quality vector PDF and PNG figures, architecture diagrams, sequence charts, and benchmark evaluation plots for the MSc Dissertation.

## Quick Start

Run the master generator using Python 3.11+:

`powershell
& C:\Users\LazyT\AppData\Local\Programs\Python\Python311\python.exe Documentos\tools\make_all.py
`

Generated figure assets are automatically placed into:
- Documentos/5-Figures/ (LaTeX compilation figure path)
- 5-Figures/ (root workspace mirror)

---

## Tool Directory Layout

| File | Purpose / Output Figures |
| :--- | :--- |
| make_all.py | **Master Suite Runner**: Executes all generators for Chapters 3, 4, and 5 sequentially. |
| 	hesis_art_utils.py | **Core Layout & Styling**: Standardized color palette, typographic hierarchy, box/card styling, automatic line wrapping, and dynamic path discovery. |
| make_architecture_conceptual.py | **Chapter 3**: Agnostic 3-layer conceptual architecture (rchitecture_conceptual.pdf). |
| un_batch1.py | **Chapter 4**: Technological realization architecture (rchitecture_global.pdf), AAS metamodel submodels, dual-mode sequence diagram, BaSyx Docker topology, and Unity scene hierarchy. |
| atch2.py | **Chapter 4**: Physical bench integration, Arduino FreeRTOS schema, pinout mappings, and wizard UI screenshots. |
| atch3.py | **Chapter 4**: Step-by-step use case interaction diagrams (Steps 1 through 5 + Aux). |
| generate_thesis_plots.py | **Chapter 5**: Benchmark plots (wizard time reduction, sync latency distribution, throughput & traffic analysis). |
| legacy/ | Archived intermediate/test scripts. |
