# download, unzip and sort an Argo DOI for consumption by ocean_pipeline.

## config ---------------
url=https://www.seanoe.org/data/00311/42182/data/125185.tar.gz # tarball you want to fetch and consume, probably from seanoe
target_dir=/scratch/alpine/wimi7695/argo_doi_2026  # where are we inflating this - needs about 2x the current size of the unpacked Argo dataset, so like 700 GB+
## ----------------------


module load slurm/blanca
mkdir -p $target_dir
wget -P $target_dir $url
tar -xzvf ${target_dir}/* -C $target_dir
for f in "$target_dir"/*/dac/*core*.tar.gz; do
    tar -xzvf "$f" -C "$target_dir"
done
mkdir ${target_dir}/sorted
for dac in aoml bodc csio incois kma meds coriolis csiro jma kiost nmdis
do
    sbatch sort_argonc.slurm $target_dir $dac
done
