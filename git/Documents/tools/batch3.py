import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thesis_art_utils import *

def make_usecase_step1():
    fig, ax = plt.subplots(figsize=(7.6, 4.0), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')
    draw_actor(ax, 9.0, 50, "Automation\nEngineer")
    draw_group(ax, 20.0, 4.0, 77.0, 92.0, "Step 1 · Select 3D Model", '#f0fdf4', '#16a34a', fs=9.5)
    draw_ellipse_uc(ax, 37.0, 70, 25, 18, "Choose GLB\n3D Model")
    draw_ellipse_uc(ax, 37.0, 30, 25, 18, "Choose URDF\nRobot Folder")
    draw_ellipse_uc(ax, 76.0, 70, 25, 18, "Preview 3D Model\nin Viewer")
    draw_ellipse_uc(ax, 76.0, 30, 25, 18, "Inspect Model\nPart Hierarchy")
    
    # Radiate from actor's right hand (x = 9.0 + 2.8 = 11.8, y = 50.8)
    draw_arrow(ax, (11.8, 50.8), (24.5, 70.0), color='#16a34a', lw=1.4)
    draw_arrow(ax, (11.8, 50.8), (24.5, 30.0), color='#16a34a', lw=1.4)
    
    draw_arrow(ax, (49.5, 70), (63.5, 70), color='#16a34a', lw=1.2, dashed=True)
    draw_badge(ax, 56.5, 76.0, "<<include>>", color='#16a34a', fs=7.0)
    draw_arrow(ax, (49.5, 30), (63.5, 30), color='#16a34a', lw=1.2, dashed=True)
    draw_badge(ax, 56.5, 36.0, "<<include>>", color='#16a34a', fs=7.0)
    save_fig(fig, "usecase_step1")

def make_usecase_step2():
    fig, ax = plt.subplots(figsize=(7.6, 4.2), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')
    draw_actor(ax, 9.0, 50, "Automation\nEngineer")
    draw_group(ax, 20.0, 4.0, 77.0, 92.0, "Step 2 · Module Info, Network & Placement", '#eff6ff', '#2563eb', fs=9.5)
    draw_ellipse_uc(ax, 37.0, 76, 25, 17, "Set Name &\nAsset ID")
    draw_ellipse_uc(ax, 37.0, 50, 25, 17, "Choose Protocol\n(TCP Stream)")
    draw_ellipse_uc(ax, 37.0, 24, 25, 17, "Set Position,\nRotation & Scale")
    draw_ellipse_uc(ax, 76.0, 50, 25, 17, "Set Network\nIP & Port 8888")
    
    # Radiate from actor's right hand
    draw_arrow(ax, (11.8, 50.8), (24.5, 76.0), color='#2563eb', lw=1.4)
    draw_arrow(ax, (11.8, 50.8), (24.5, 50.0), color='#2563eb', lw=1.4)
    draw_arrow(ax, (11.8, 50.8), (24.5, 24.0), color='#2563eb', lw=1.4)
    
    draw_arrow(ax, (49.5, 50), (63.5, 50), color='#2563eb', lw=1.2, dashed=True)
    draw_badge(ax, 56.5, 56.0, "<<include>>", color='#2563eb', fs=7.0)
    save_fig(fig, "usecase_step2")

def make_usecase_step3():
    fig, ax = plt.subplots(figsize=(7.6, 4.4), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')
    draw_actor(ax, 8.5, 50, "Automation\nEngineer")
    draw_group(ax, 19.0, 4.0, 78.0, 92.0, "Step 3 · Setup Sensors (Input Pins)", '#faf5ff', '#9333ea', fs=9.5)
    draw_ellipse_uc(ax, 35.0, 68, 25, 19, "Add Sensor\n(Optical / Prox)")
    draw_ellipse_uc(ax, 35.0, 26, 25, 19, "Edit or Remove\nSensor Binding")
    draw_ellipse_uc(ax, 77.0, 78, 25, 17, "Map Input Pin\n(I0_0 to I2_5)")
    draw_ellipse_uc(ax, 77.0, 51, 25, 17, "Attach to Part\nin 3D Model")
    draw_ellipse_uc(ax, 77.0, 24, 25, 17, "Set Trigger Logic\n& Part Snapping")
    
    # Radiate from actor's right hand (x = 8.5 + 2.8 = 11.3, y = 50.8)
    draw_arrow(ax, (11.3, 50.8), (22.5, 68.0), color='#9333ea', lw=1.4)
    draw_arrow(ax, (11.3, 50.8), (22.5, 26.0), color='#9333ea', lw=1.4)
    
    draw_arrow(ax, (47.5, 74), (64.5, 78), color='#9333ea', lw=1.2, dashed=True)
    draw_badge(ax, 56.0, 79.5, "<<include>>", color='#9333ea', fs=6.8)
    draw_arrow(ax, (47.5, 68), (64.5, 51), color='#9333ea', lw=1.2, dashed=True)
    draw_badge(ax, 56.0, 63.0, "<<include>>", color='#9333ea', fs=6.8)
    draw_arrow(ax, (47.5, 62), (64.5, 26), color='#9333ea', lw=1.2, dashed=True)
    draw_badge(ax, 56.0, 42.0, "<<extend>>", color='#9333ea', fs=6.8)
    save_fig(fig, "usecase_step3")

def make_usecase_step4():
    fig, ax = plt.subplots(figsize=(7.6, 4.4), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')
    draw_actor(ax, 8.5, 50, "Automation\nEngineer")
    draw_group(ax, 19.0, 4.0, 78.0, 92.0, "Step 4 · Setup Actuators (Output Pins)", '#fffbeb', '#b45309', fs=9.5)
    draw_ellipse_uc(ax, 35.0, 68, 25, 19, "Add Actuator\n(Belt / Stopper)")
    draw_ellipse_uc(ax, 35.0, 26, 25, 19, "Edit or Remove\nActuator Binding")
    draw_ellipse_uc(ax, 77.0, 78, 25, 17, "Map Output Pin\n(R0_2 to R2_8)")
    draw_ellipse_uc(ax, 77.0, 51, 25, 17, "Select Moving Surface\nin 3D Model")
    draw_ellipse_uc(ax, 77.0, 24, 25, 17, "Set Belt Speed &\nDirection")
    
    # Radiate from actor's right hand
    draw_arrow(ax, (11.3, 50.8), (22.5, 68.0), color='#b45309', lw=1.4)
    draw_arrow(ax, (11.3, 50.8), (22.5, 26.0), color='#b45309', lw=1.4)
    
    draw_arrow(ax, (47.5, 74), (64.5, 78), color='#b45309', lw=1.2, dashed=True)
    draw_badge(ax, 56.0, 79.5, "<<include>>", color='#b45309', fs=6.8)
    draw_arrow(ax, (47.5, 68), (64.5, 51), color='#b45309', lw=1.2, dashed=True)
    draw_badge(ax, 56.0, 63.0, "<<include>>", color='#b45309', fs=6.8)
    draw_arrow(ax, (47.5, 62), (64.5, 26), color='#b45309', lw=1.2, dashed=True)
    draw_badge(ax, 56.0, 42.0, "<<extend>>", color='#b45309', fs=6.8)
    save_fig(fig, "usecase_step4")

def make_usecase_step5():
    fig, ax = plt.subplots(figsize=(7.6, 4.6), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')
    draw_actor(ax, 7.5, 50, "Automation\nEngineer")
    draw_group(ax, 15.0, 3.0, 56.0, 94.0, "Step 5 · Build & Publish Digital Twin", '#fef2f2', '#dc2626', fs=9.5)

    # Build Column (inside group: x = 15.0 to 71.0)
    draw_ellipse_uc(ax, 27.5, 75, 21.0, 17.0, "1. Check Pin\n& Config Setup")
    draw_ellipse_uc(ax, 27.5, 50, 21.0, 17.0, "2. Create AAS\nSubmodels")
    draw_ellipse_uc(ax, 27.5, 25, 21.0, 17.0, "3. Package AASX\nFile with 3D Parts")

    # Deploy Column
    draw_ellipse_uc(ax, 56.5, 75, 21.0, 17.0, "4. Check Name in\nAAS Server")
    draw_ellipse_uc(ax, 56.5, 50, 21.0, 17.0, "5. Upload AASX\nvia REST")
    draw_ellipse_uc(ax, 56.5, 25, 21.0, 17.0, "6. Register Shell\nOnline")

    # External BaSyx Systems (outside group: x = 74.0 to 97.5)
    draw_card(ax, 74.0, 53.0, 23.5, 23.0, "BaSyx Server", ["• Port 8081", "• Stores AASX", "• REST API"], bg='#eff6ff', border='#2563eb', t_fs=8.5, b_fs=7.2)
    draw_card(ax, 74.0, 17.0, 23.5, 23.0, "BaSyx Registry", ["• Port 8082", "• Asset Catalog", "• Shell Index"], bg='#faf5ff', border='#9333ea', t_fs=8.5, b_fs=7.2)

    # Radiate from actor's right hand (x = 7.5 + 2.8 = 10.3, y = 50.8)
    draw_arrow(ax, (10.3, 50.8), (17.0, 75.0), color='#dc2626', lw=1.4)
    
    draw_arrow(ax, (27.5, 66.5), (27.5, 58.5), color='#dc2626', lw=1.2, dashed=True)
    draw_badge(ax, 27.5, 62.5, "<<include>>", color='#dc2626', fs=6.5)

    draw_arrow(ax, (27.5, 41.5), (27.5, 33.5), color='#dc2626', lw=1.2, dashed=True)
    draw_badge(ax, 27.5, 37.5, "<<include>>", color='#dc2626', fs=6.5)

    draw_arrow(ax, (38.0, 25.0), (46.0, 75.0), color='#dc2626', lw=1.4)
    draw_badge(ax, 42.0, 50.0, "Ready", color='#dc2626', fs=7.2)

    draw_arrow(ax, (56.5, 66.5), (56.5, 58.5), color='#dc2626', lw=1.2, dashed=True)
    draw_badge(ax, 56.5, 62.5, "<<include>>", color='#dc2626', fs=6.5)

    draw_arrow(ax, (56.5, 41.5), (56.5, 33.5), color='#dc2626', lw=1.2, dashed=True)
    draw_badge(ax, 56.5, 37.5, "<<include>>", color='#dc2626', fs=6.5)

    draw_arrow(ax, (67.0, 50.0), (74.0, 62.0), color='#2563eb', lw=1.4)
    draw_arrow(ax, (67.0, 25.0), (74.0, 27.0), color='#9333ea', lw=1.4)
    save_fig(fig, "usecase_step5")

def make_usecase_aux():
    fig, ax = plt.subplots(figsize=(7.6, 4.2), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')
    draw_actor(ax, 9.0, 50, "Automation\nEngineer")
    draw_group(ax, 20.0, 4.0, 77.0, 92.0, "Extra Operations · Layout Studio & Logic Rules", '#f8fafc', '#475569', fs=9.5)
    draw_ellipse_uc(ax, 37.0, 76, 26, 17, "Manage Saved\nTwin Models")
    draw_ellipse_uc(ax, 37.0, 50, 26, 17, "Open Plant\nLayout Studio")
    draw_ellipse_uc(ax, 37.0, 24, 26, 17, "Open Logic Rules\n(IF / THEN Tables)")
    draw_ellipse_uc(ax, 77.0, 50, 26, 17, "Snap & Align Parts\nin 3D Scene")
    draw_ellipse_uc(ax, 77.0, 24, 26, 17, "Export Rules to\nUnity Logic Script")

    # Radiate from actor's right hand
    draw_arrow(ax, (11.8, 50.8), (24.0, 76.0), color='#475569', lw=1.4)
    draw_arrow(ax, (11.8, 50.8), (24.0, 50.0), color='#475569', lw=1.4)
    draw_arrow(ax, (11.8, 50.8), (24.0, 24.0), color='#475569', lw=1.4)
    
    draw_arrow(ax, (50.0, 50.0), (64.0, 50.0), color='#475569', lw=1.2, dashed=True)
    draw_badge(ax, 57.0, 56.0, "<<include>>", color='#475569', fs=7.0)
    draw_arrow(ax, (50.0, 24.0), (64.0, 24.0), color='#475569', lw=1.2, dashed=True)
    draw_badge(ax, 57.0, 30.0, "<<include>>", color='#475569', fs=7.0)
    save_fig(fig, "usecase_aux")

if __name__ == "__main__":
    make_usecase_step1()
    make_usecase_step2()
    make_usecase_step3()
    make_usecase_step4()
    make_usecase_step5()
    make_usecase_aux()
    print("Batch 3 completed successfully.")

