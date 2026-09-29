@echo off
echo ===================================================
echo Converting Mermaid (.mmd) diagrams to PDF / PNG...
echo ===================================================

if not exist "..\Figures" mkdir "..\Figures"
if not exist "..\5-Figures" mkdir "..\5-Figures"

for %%f in (*.mmd) do (
    echo Processing: %%f
    call npx -y @mermaid-js/mermaid-cli -i "%%f" -o "..\Figures\%%~nf.pdf" --pdfFit -c "mermaid_config.json" -C "diagram_style.css"
    call npx -y @mermaid-js/mermaid-cli -i "%%f" -o "..\Figures\%%~nf.png" -s 3 -c "mermaid_config.json" -C "diagram_style.css"
    copy /Y "..\Figures\%%~nf.pdf" "..\5-Figures\%%~nf.pdf" >nul
    copy /Y "..\Figures\%%~nf.png" "..\5-Figures\%%~nf.png" >nul
)

echo.
echo ===================================================
echo All diagrams successfully converted to ..\Figures\ and ..\5-Figures\
echo ===================================================
