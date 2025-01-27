Generate the shell commands and json files
On a transfer node

```
python google_drive_exports_csv_qc.py cp_tif 1> step0_on_transfer.sh
python google_drive_exports_csv_qc.py templates 1> step1_on_transfer.sh
python google_drive_exports_csv_qc.py transfer 1> step2_on_transfer.sh
python google_drive_exports_csv_qc.py cp_output 1> step3_anywhere.sh
python google_drive_exports_csv_qc.py json
```

Run the resulting shell commands and schedule jobs.

```
bash step0_on_transfer.sh
bash step1_on_transfer.sh

for f in roi/*.bash; do sbatch ${f}; done;
for f in render/*.bash; do sbatch ${f}; done;
```

Wait for slurm jobs to complete and run shell commands.

```
bash step2_on_transfer.sh
bash step3_anywhere.sh
```
