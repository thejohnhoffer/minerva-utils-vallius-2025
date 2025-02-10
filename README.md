Generate the shell commands and json files
On a transfer node

```
python google_drive_exports_csv_qc.py cp_tif 1> step0_on_transfer.sh
python google_drive_exports_csv_qc.py templates 1> step1_on_transfer.sh
python google_drive_exports_csv_qc.py cp_output 1> step2_anywhere.sh
python google_drive_exports_csv_qc.py json
```

Run the resulting shell commands and schedule jobs.

```
bash step0_on_transfer.sh
bash step1_on_transfer.sh
```

```
for f in render/stage_ii_p135*; do sbatch ${f}; done;
for f in roi/stage_ii_p135*; do sbatch ${f}; done;
bash transfer_and_delete.sh
```

```
for f in render/stage_ii_tumor*; do sbatch ${f}; done;
for f in roi/stage_ii_tumor*; do sbatch ${f}; done;
bash transfer_and_delete.sh
```

```
for f in render/early_melanoma_he*; do sbatch ${f}; done;
for f in roi/early_melanoma_he*; do sbatch ${f}; done;
bash transfer_and_delete.sh
```

```
for f in render/early_melanoma_cell*; do sbatch ${f}; done;
for f in roi/early_melanoma_cell*; do sbatch ${f}; done;
bash transfer_and_delete.sh
```

On a transfer node:
```
aws s3 sync s3://www.cycif.org/vallius-2025/ /n/scratch/users/j/jth30/2024-12-16/vallius-2025 --exclude "*" --include "*.json"
```

Wait for slurm jobs to complete and run shell commands.

```
bash step2_anywhere.sh
```
