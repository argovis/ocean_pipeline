#!/bin/bash
#SBATCH --qos=preemptable
#SBATCH --export=NONE
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=24:00:00
#SBATCH --job-name=qc-pipeline
#SBATCH --output=%x.%j.out
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=katie.mills@colorado.edu
#SBATCH --mem=32GB
#SBATCH --exclude=blanca-g4-u6-2,blanca-g4-u14-1

module purge
module load anaconda/2023.09
conda activate wod2mat

cd $SLURM_SUBMIT_DIR
python wod_input.py --data_dir $1 --year $2 --month $3 --filetypes $4 --pressure_qc $5 --temperature_qc $6 --salinity_qc $7 --output_file $8
