Generate the shell commands and json files
On a transfer node

```
python google_drive_exports_csv_qc.py cp_tif 1> step0_on_transfer.sh
python google_drive_exports_csv_qc.py copy 1> step1_on_login.sh
python google_drive_exports_csv_qc.py transfer 1> step3_on_transfer.sh
python google_drive_exports_csv_qc.py cp_output 1> step4_anywhere.sh
python google_drive_exports_csv_qc.py json
```

Run the output shell commands

```
bash step0_on_transfer.sh
bash step1_on_login.sh
bash step2_on_transfer.sh
bash step3_anywhere.sh
```
