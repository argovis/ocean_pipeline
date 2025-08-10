#!/bin/bash
#SBATCH --qos=blanca-giglio
#SBATCH --account=blanca-giglio
#SBATCH --partition=blanca-giglio
#SBATCH --export=NONE
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=168:00:00
#SBATCH --job-name=nc_sort
#SBATCH --output=%x.%j.out
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=katie.mills@colorado.edu
#SBATCH --mem=32GB
#SBATCH --exclude=bnode0508,bnode0509

module purge
module load anaconda/2023.09
conda activate wod2mat

cd $SLURM_SUBMIT_DIR
#dac options are: aoml bodc csio incois kma meds coriolis csiro jma kordi nmdis
python sort_argonc.py /scratch/alpine/wimi7695/argo_doi_2025/202501-ArgoData/dac/aoml /scratch/alpine/wimi7695/argo_doi_2025/sorted
