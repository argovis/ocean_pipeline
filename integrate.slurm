#!/bin/bash
#SBATCH --qos=preemptable
#SBATCH --export=NONE
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=24:00:00
#SBATCH --job-name=integrate-wod2mat
#SBATCH --output=%x.%j.out
#SBATCH --mail-type=END
#SBATCH --mail-user=katie.mills@colorado.edu
#SBATCH --mem=16GB

module purge
module load anaconda/2023.09
conda activate wod2mat

cd $SLURM_SUBMIT_DIR
python integrate.py --input_file $1 --regions $2 --variables $3
