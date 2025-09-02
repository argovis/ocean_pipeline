#!/bin/bash
#SBATCH --qos=preemptable
#SBATCH --export=NONE
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=12:00:00
#SBATCH --job-name=integrate-pipeline
#SBATCH --output=%x.%j.out
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=katie.mills@colorado.edu
#SBATCH --mem=16GB
#SBATCH --exclude=blanca-g4-u6-2,blanca-g4-u14-1

module purge
module load anaconda/2023.09
conda activate wod2mat

cd $SLURM_SUBMIT_DIR
python integrate.py --input_file $1 --region $2 --variable $3 --output_file $4
