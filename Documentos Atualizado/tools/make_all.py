# -*- coding: utf-8 -*-
"""
Master Generator for All Thesis Figures and Plots
Orchestrates Chapter 3 conceptual architecture, Chapter 4 realization diagrams, and Chapter 5 benchmark plots.
"""
import os
import sys

# Ensure local imports resolve
tools_dir = os.path.dirname(os.path.abspath(__file__))
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

import make_architecture_conceptual
import run_batch1
import batch2
import batch3
import generate_thesis_plots
import generate_chapter5_eval_plots

def main():
    print("==========================================================")
    print("      FULL THESIS FIGURE & PLOT GENERATION SUITE          ")
    print("==========================================================")

    print("\n[1/5] Generating Chapter 3: Conceptual Architecture & Metamodel...")
    make_architecture_conceptual.make_architecture_conceptual()
    make_architecture_conceptual.make_asset_metamodel_conceptual()

    print("\n[2/5] Generating Chapter 4: Technological Architecture & Metamodels...")
    run_batch1.make_architecture_global()
    run_batch1.make_aas_metamodel_submodels()
    run_batch1.make_dual_mode_sequence()
    run_batch1.make_basyx_docker_topology()
    run_batch1.make_unity_scene_hierarchy()

    print("\n[3/5] Generating Chapter 4: Physical Integration & Wizard UI...")
    batch2.make_arduino_freertos_schema()
    batch2.make_fms_physical_bench()
    batch2.make_fms_sensor_actuator_details()
    batch2.make_wizard_ui_screenshots()

    print("\n[4/5] Generating Chapter 4: Use Case Step Diagrams...")
    batch3.make_usecase_step1()
    batch3.make_usecase_step2()
    batch3.make_usecase_step3()
    batch3.make_usecase_step4()
    batch3.make_usecase_step5()
    batch3.make_usecase_aux()

    print("\n[5/5] Generating Chapter 5: Experimental Evaluation Plots...")
    generate_thesis_plots.plot_manual_vs_wizard_time()
    generate_thesis_plots.plot_sync_latency_boxplot()
    generate_thesis_plots.plot_traffic_overhead_analysis()
    generate_chapter5_eval_plots.main()

    print("\n==========================================================")
    print("  ALL THESIS FIGURES & PLOTS GENERATED SUCCESSFULLY!      ")
    print("==========================================================")

if __name__ == "__main__":
    main()
