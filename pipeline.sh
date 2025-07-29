# pipeline to compile all the source data found in data_dir into files appropriate for localGP, including data selection, variable computation, interpolation, integration and downsampling.
# note data_dir should start with one month worth of upstream data, if you expect to get localGP inputs organized by month.
# typically call this script from a loop over year and month.
declare vartype='integration'	 		# 'integration', 'interpolation', or 'none' (if no interpoltions or integrations needed)
declare upstream='argonc' 			# 'argovis', 'wod' or 'argonc'
declare data_dir=$1				# where is the relevant upstream data?
declare year=$2					# year this data corresponds to
declare month=$3				# month this data corresponds to
declare wod_filetypes='PFL,MRB,CTD'		# WOD filetypes, wod only
declare level=10				# dbar to interpolate to in interpolation mode
declare pqc=0					# qc to keep for pressure, wod only, can be single valued (0) or string CSV ('0,1')
declare tqc=0					# qc to keep for temeprature, wod only
declare sqc='0,1'				# qc to keep for salinity, wod only
declare region='15,300'				# integration dbar region, string CSV, in integration mode
declare variable='potential_temperature'	# 'absolute_salinity', 'potential_temperature', 'conservative_temperature', 'potential_density', 'mld'

# data prep
if [[ $upstream == 'wod' ]]; then
    declare prep_id=$(sbatch --parsable wod.slurm $data_dir $year $month $wod_filetypes $pqc $tqc $sqc)
    qcfile=${data_dir}/${month}_p${pqc//,/_}_t${tqc//,/_}_s${sqc//,/_}_profiles.parquet
elif [[ $upstream == 'argovis' ]]; then
    declare prep_id=$(sbatch --parsable argovis.slurm $data_dir $year $month)
    qcfile=${data_dir}/${month}_p${pqc//,/_}_t${tqc//,/_}_s${sqc//,/_}_profiles.parquet
elif [[ $upstream == 'argonc' ]]; then
    declare prep_id=$(sbatch --parsable argonc.slurm $year $month $data_dir)
    qcfile=${data_dir}/demo_${year}_${month}.parquet
fi

varfile=${data_dir}/${month}_${variable}.parquet
declare varcreation=$(sbatch --parsable --dependency=afterok:$prep_id variable_creation.slurm $qcfile $variable ${varfile})
#declare varcreation=$(sbatch --parsable variable_creation.slurm $qcfile $variable ${varfile})

if [[ $vartype == 'interpolation' ]]; then
    interpfile=${data_dir}/${month}_${variable}_interpolated_${level}.parquet
    interp_downsampled=${data_dir}/${month}_${variable}_interpolated_${level}_downsampled.parquet
    interp_matlab=${data_dir}/${month}_${variable}_interpolated_${level}.mat
    declare interpolation=$(sbatch --parsable --dependency=afterok:$varcreation interpolate.slurm $varfile $level $variable $interpfile)
    declare downsample=$(sbatch --parsable --dependency=afterok:$interpolation downsample.slurm $interpfile $interp_downsampled)
    sbatch --dependency=afterok:$downsample matlab.slurm $interp_downsampled $interp_matlab ${variable}_interpolation
elif [[ $vartype == 'integration' ]]; then
    region_tag=${region/,/_}
    integfile=${data_dir}/${month}_${variable}_integrated_${region_tag}.parquet
    integ_downsampled=${data_dir}/${month}_${variable}_integrated_${region_tag}_downsampled.parquet
    integ_matlab=${data_dir}/${month}_${variable}_integrated_${region_tag}.mat
    declare integration=$(sbatch --parsable --dependency=afterok:$varcreation integrate.slurm $varfile $region $variable $integfile)
    declare downsample=$(sbatch --parsable --dependency=afterok:$integration downsample.slurm $integfile $integ_downsampled)
    sbatch --dependency=afterok:$downsample matlab.slurm $integ_downsampled $integ_matlab ${variable}_integration
elif [[ $vartype == 'none' ]]; then
    var_downsampled=${data_dir}/${month}_${variable}_downsampled.parquet
    var_matlab=${data_dir}/${month}_${variable}.mat
    declare downsample=$(sbatch --parsable --dependency=afterok:$varcreation downsample.slurm $varfile $var_downsampled)
    sbatch --dependency=afterok:$downsample matlab.slurm $var_downsampled $var_matlab ${variable}
fi
