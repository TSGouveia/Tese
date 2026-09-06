@echo off
echo ===================================================
echo Compiling PlantUML (.puml) diagrams to SVG & Vector PDF...
echo ===================================================

if not exist "..\Figures" mkdir "..\Figures"

for %%f in (*.puml) do (
    echo Processing: %%f
    java -jar plantuml.jar -tsvg "%%f" -o "..\Figures"
)

echo Converting SVGs to vector PDFs via Python...
python -c "import glob; from svglib.svglib import svg2rlg; from reportlab.graphics import renderPDF; [renderPDF.drawToFile(svg2rlg(f), f.rsplit('.',1)[0]+'.pdf') for f in glob.glob('../Figures/*.svg')]"

echo.
echo ===================================================
echo Finished compiling PlantUML vector diagrams!
echo ===================================================
