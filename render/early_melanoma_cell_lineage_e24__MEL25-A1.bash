#!/bin/bash
#SBATCH -c 4
#SBATCH -p short
#SBATCH --mem 4g
#SBATCH -e slurm-%A_%a.err
#SBATCH -o slurm-%A_%a.out
#SBATCH -t 3:00:00
#SBATCH --array=0-0
DATE="2024-12-16"
URL_ROOT="early_melanoma_cell_lineage_e24"
IDENTIFIER="MEL25-A1"
SAMPLE="LSP11403"
