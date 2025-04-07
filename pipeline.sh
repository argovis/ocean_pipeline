declare data_dir=/scratch/alpine/wimi7695/wod/2017
declare levels='100,200'
declare regions='50,100 100,150'
declare interpolation_variables='temperature salinity'
declare integration_variables='absolute_salinity conservative_temperature'

qc_id=$(sbatch --parsable qc.slurm $data_dir)

for i in {1..12}; do
    qcfile=${data_dir}/${i}_QC0_profiles.parquet
    declare varcreation=$(sbatch --parsable --dependency=afterok:$qc_id variable_creation.slurm $qcfile)

    varfile=${data_dir}/${i}_QC0_profiles_derived.parquet
    declare interpolation_${i}=$(sbatch --parsable --dependency=afterok:$varcreation interpolate.slurm $varfile $levels "$interpolation_variables")
    declare integration_${i}=$(sbatch --parsable --dependency=afterok:$varcreation integrate.slurm $varfile "$regions" "$integration_variables")
done
