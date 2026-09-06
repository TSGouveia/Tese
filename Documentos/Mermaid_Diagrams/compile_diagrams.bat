@echo off
echo ===================================================
echo Converting Mermaid (.mmd) diagrams to PDF / PNG...
echo ===================================================

if not exist "..\Figures" mkdir "..\Figures"

for %%f in (*.mmd) do (
    echo Processing: %%f
    call mmdc -i "%%f" -o "..\Figures\%%~nf.pdf" --pdfFit
    call mmdc -i "%%f" -o "..\Figures\%%~nf.png"
)

echo.
echo ===================================================
echo All diagrams successfully converted to ..\Figures\
echo ===================================================
