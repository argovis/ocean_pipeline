declare data_dir=$1
declare level=5
#declare region='100,150'
declare variable='salinity'

#qc_id=$(sbatch --parsable qc.slurm $data_dir)

for i in {1..12}; do
    #rm ${data_dir}/*.parquet
    qcfile=${data_dir}/${i}_QC0_profiles.parquet
    varfile=${data_dir}/${i}_${variable}.parquet
    #declare varcreation=$(sbatch --parsable --dependency=afterok:$qc_id variable_creation.slurm $qcfile $variable ${varfile})
    declare varcreation=$(sbatch --parsable variable_creation.slurm $qcfile $variable ${varfile})

    # interpolation
    interpfile=${data_dir}/${i}_${variable}_interpolated_${level}.parquet
    interp_downsampled=${data_dir}/${i}_${variable}_interpolated_${level}_downsampled.parquet
    declare interpolation=$(sbatch --parsable --dependency=afterok:$varcreation interpolate.slurm $varfile $level $variable $interpfile)
    sbatch --dependency=afterok:$interpolation downsample.slurm $interpfile $interp_downsampled
    
    # integration
    # region_tag = ${region/,/_}
    # integfile=${data_dir}/${i}_${variable}_integrated_${region_tag}.parquet
    # integ_downsampled=${data_dir}/${i}_${variable}_integrated_${region_tag}_downsampled.parquet
    # declare integration=$(sbatch --parsable --dependency=afterok:$varcreation integrate.slurm $varfile $region $variable $integfile)
    # sbatch --dependency=afterok:$integration downsample.slurm $integfile $integ_downsampled
done
