declare data_dir=/scratch/alpine/wimi7695/wod/2017
declare level=100
declare region='100,150'
declare variable='potential_temperature'

qc_id=$(sbatch --parsable qc.slurm $data_dir)

for i in {1..12}; do
    qcfile=${data_dir}/${i}_QC0_profiles.parquet
    declare varcreation=$(sbatch --parsable --dependency=afterok:$qc_id variable_creation.slurm $qcfile $variable)

    varfile=${data_dir}/${i}_QC0_profiles_${args.variable}.parquet
    declare interpolation_${i}=$(sbatch --parsable --dependency=afterok:$varcreation interpolate.slurm $varfile $level $variable)
    declare integration_${i}=$(sbatch --parsable --dependency=afterok:$varcreation integrate.slurm $varfile $region $variable)
done
