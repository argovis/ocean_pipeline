declare vartype='integration'	 		# 'integration' or 'interpolation'
declare upstream='argovis' 			# 'argovis' or 'wod'
declare data_dir=$1				# where is a year of upstream data?
declare wod_filetypes='PFL,MRB,CTD'		# WOD filetypes, wod only
declare level=10				# dbar to interpolate to in interpolation mode
declare pqc=0					# qc to keep for pressure, wod only, can be single valued (0) or string CSV ('0,1')
declare tqc=0					# qc to keep for temeprature, wod only
declare sqc='0,1'					# qc to keep for salinity, wod only
declare region='1800,1850'				# integration dbar region, string CSV, in integration mode
declare variable='potential_temperature'	# 'absolute_salinity', 'potential_temperature', or 'conservative_temperature'

# data prep
if [[ $upstream == 'wod' ]]; then
    declare prep_id=$(sbatch --parsable wod.slurm $data_dir $wod_filetypes $pqc $tqc $sqc)
elif [[ $upstream == 'argovis' ]]; then
    declare prep_id=$(sbatch --parsable argovis.slurm $data_dir)
fi

# one pipeline for every month in the year
for i in {1..12}; do
    qcfile=${data_dir}/${i}_p${pqc//,/_}_t${tqc//,/_}_s${sqc//,/_}_profiles.parquet
    varfile=${data_dir}/${i}_${variable}.parquet
    declare varcreation=$(sbatch --parsable --dependency=afterok:$prep_id variable_creation.slurm $qcfile $variable ${varfile})
    #declare varcreation=$(sbatch --parsable variable_creation.slurm $qcfile $variable ${varfile})

    if [[ $vartype == 'interpolation' ]]; then
        interpfile=${data_dir}/${i}_${variable}_interpolated_${level}.parquet
        interp_downsampled=${data_dir}/${i}_${variable}_interpolated_${level}_downsampled.parquet
        interp_matlab=${data_dir}/${i}_${variable}_interpolated_${level}.mat
        declare interpolation=$(sbatch --parsable --dependency=afterok:$varcreation interpolate.slurm $varfile $level $variable $interpfile)
        declare downsample=$(sbatch --parsable --dependency=afterok:$interpolation downsample.slurm $interpfile $interp_downsampled)
        sbatch --dependency=afterok:$downsample matlab.slurm $interp_downsampled $interp_matlab ${variable}_interpolation
    elif [[ $vartype == 'integration' ]]; then
        region_tag=${region/,/_}
        integfile=${data_dir}/${i}_${variable}_integrated_${region_tag}.parquet
        integ_downsampled=${data_dir}/${i}_${variable}_integrated_${region_tag}_downsampled.parquet
        integ_matlab=${data_dir}/${i}_${variable}_integrated_${region_tag}.mat
        declare integration=$(sbatch --parsable --dependency=afterok:$varcreation integrate.slurm $varfile $region $variable $integfile)
        declare downsample=$(sbatch --parsable --dependency=afterok:$integration downsample.slurm $integfile $integ_downsampled)
        sbatch --dependency=afterok:$downsample matlab.slurm $integ_downsampled $integ_matlab ${variable}_integration
    fi
done
