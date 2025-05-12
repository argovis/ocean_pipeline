declare data_dir=$1
#declare level=10
declare pqc=0
declare tqc=0
declare sqc='0,1'
declare region='15,300'
declare variable='potential_temperature'

# wod input - needs qc
# set which datasets you want in qc_filter.py; TODO, make that an option here.
#qc_id=$(sbatch --parsable qc.slurm $data_dir $pqc $tqc $sqc)

# argovis input - qc performed by API
qc_id=$(sbatch --parsable argo.slurm $data_dir)

for i in {1..12}; do
    #rm ${data_dir}/*.parquet
    #rm ${data_dir}/*.mat
    qcfile=${data_dir}/${i}_p${pqc//,/_}_t${tqc//,/_}_s${sqc//,/_}_profiles.parquet
    varfile=${data_dir}/${i}_${variable}.parquet
    declare varcreation=$(sbatch --parsable --dependency=afterok:$qc_id variable_creation.slurm $qcfile $variable ${varfile})
    #declare varcreation=$(sbatch --parsable variable_creation.slurm $qcfile $variable ${varfile})

    # interpolation
    #interpfile=${data_dir}/${i}_${variable}_interpolated_${level}.parquet
    #interp_downsampled=${data_dir}/${i}_${variable}_interpolated_${level}_downsampled.parquet
    #interp_matlab=${data_dir}/${i}_${variable}_interpolated_${level}.mat
    #declare interpolation=$(sbatch --parsable --dependency=afterok:$varcreation interpolate.slurm $varfile $level $variable $interpfile)
    #declare downsample=$(sbatch --parsable --dependency=afterok:$interpolation downsample.slurm $interpfile $interp_downsampled)
    #sbatch --dependency=afterok:$downsample matlab.slurm $interp_downsampled $interp_matlab ${variable}_interpolation

    # integration
    region_tag=${region/,/_}
    integfile=${data_dir}/${i}_${variable}_integrated_${region_tag}.parquet
    integ_downsampled=${data_dir}/${i}_${variable}_integrated_${region_tag}_downsampled.parquet
    integ_matlab=${data_dir}/${i}_${variable}_integrated_${region_tag}.mat
    declare integration=$(sbatch --parsable --dependency=afterok:$varcreation integrate.slurm $varfile $region $variable $integfile)
    declare downsample=$(sbatch --parsable --dependency=afterok:$integration downsample.slurm $integfile $integ_downsampled)
    sbatch --dependency=afterok:$downsample matlab.slurm $integ_downsampled $integ_matlab ${variable}_integration
done
