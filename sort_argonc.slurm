#!/bin/bash
#SBATCH --qos=blanca-giglio
#SBATCH --account=blanca-giglio
#SBATCH --partition=blanca-giglio
#SBATCH --export=NONE
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8
#SBATCH --time=24:00:00
#SBATCH --job-name=nc_sort
#SBATCH --output=%x.%j.out
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=katie.mills@colorado.edu
#SBATCH --mem=32GB
#SBATCH --exclude=blanca-g4-u6-2,blanca-g4-u14-1

module purge
module load anaconda/2023.09
conda activate wod2mat

cd $SLURM_SUBMIT_DIR
#python sort_argonc.py $1/$2 $1/sorted
python sort_argonc_parallel.py $1/$2 $1/sorted
