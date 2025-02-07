#!/bin/bash
#SBATCH -c 4
#SBATCH -p short
#SBATCH --mem 4g
#SBATCH -e slurm-%A_%a.err
#SBATCH -o slurm-%A_%a.out
#SBATCH -t 2:00:00
