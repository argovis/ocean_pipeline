declare data_dir=$1
declare level=5
declare pqc=0
declare tqc=0
declare sqc='0,1'
#declare region='100,150'
declare variable='salinity'

qc_id=$(sbatch --parsable qc.slurm $data_dir $pqc $tqc $sqc)

for i in {1..12}; do
    #rm ${data_dir}/*.parquet
    qcfile=${data_dir}/${i}_QC0_profiles.parquet
    varfile=${data_dir}/${i}_${variable}.parquet
    declare varcreation=$(sbatch --parsable --dependency=afterok:$qc_id variable_creation.slurm $qcfile $variable ${varfile})

    # interpolation
    interpfile=${data_dir}/${i}_${variable}_interpolated_${level}.parquet
    interp_downsampled=${data_dir}/${i}_${variable}_interpolated_${level}_downsampled.parquet
    interp_matlab=${data_dir}/${i}_${variable}_interpolated_${level}.mat
    declare interpolation=$(sbatch --parsable --dependency=afterok:$varcreation interpolate.slurm $varfile $level $variable $interpfile)
    declare downsample=$(sbatch --parsable --dependency=afterok:$interpolation downsample.slurm $interpfile $interp_downsampled)
    sbatch --dependency=afterok:$downsample matlab.slurm $interp_downsampled $interp_matlab $variable
    
    # integration
    # region_tag = ${region/,/_}
    # integfile=${data_dir}/${i}_${variable}_integrated_${region_tag}.parquet
    # integ_downsampled=${data_dir}/${i}_${variable}_integrated_${region_tag}_downsampled.parquet
    # integ_matlab=${data_dir}/${i}_${variable}_integrated_${region_tag}.mat
    # declare integration=$(sbatch --parsable --dependency=afterok:$varcreation integrate.slurm $varfile $region $variable $integfile)
    # declare downsample=$(sbatch --parsable --dependency=afterok:$integration downsample.slurm $integfile $integ_downsampled)
    # sbatch --dependency=afterok:$downsample matlab.slurm $integ_downsampled $integ_matlab $variable
done
