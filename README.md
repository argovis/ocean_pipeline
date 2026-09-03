# ocean-pipeline

This repo provides pipelines to consume several different data sources and clean, interpolate, and derrive quantities of interest in preparation for consumption for a downstream consumer.

## Overview

Pipelines in this repo typically consist of a few steps:

 - Data acquisition / sorting: download links, scripts or other info for getting the raw data from an upstream provider, and organizing in a rational manner (typically one subdirectory per month of raw data).
 - Processing pipeline: a series of serially dependent slurm scripts that manage the main transforms, typically data cleaning and selection -> derived variable construction -> interpolation and integration -> downsampling -> output format construction.

As is generically true for essentially all data pipelines, *provenance is crucial*. Provenance records will look a bit different for each pipeline, but make sure to keep records of, at least:
 - how to acquire the original upstream data (DOIs are the gold standard)
 - what parameters were used in the pipeline
 - git hash or release of the codebase of this repo reflecting its *exact* state when the pipeline was ran.

the `provenance/` subdirectory here is an appropriate place for these records.

## Argo netCDF -> localGP

Argo's GDACs provide the complete Argo dataset as netCDF files; they also publish a [DOI-stamped release](https://www.seanoe.org/data/00311/42182/) regularly. Prep this data for localGP as follows:

### 1. Downlaod & sort (1 / Argo DOI)

Set the config varibles at the top of `dl_sort.sh` and run it to download a tarball of Argo data, unpack it, and sort it into monthly bins as ocean_pipeline expects. Takes a few hours. Tips:

- Feel free to delete the tarball and its unpacked directories once the process is complete; you'll only need the copy that lands under `${target_dir}/sorted`.
- You'll probably want to do this on `/scratch`, but if you have the allocation to spare, copy the reuslt over to `/pl` so you don't have to redo this every 3 months when files age out on scratch.

### 2. Processing pipeline (1 / LocalGP map)

Once input netCDF files are sorted by month, `launch_localgp_pipelines.sh` supports preparing these files for consumption by localGP:

 - Start by setting appropriate variables for this run in the block at the top of `launch_localgp_pipelines.sh`. There are some others at the top of `pipeline4localgp.sh` which you can probably leave alone.
 - Run `bash launch_localgp_pipelines.sh` to launch an appropriate pipeline of jobs for the study period on a slurm-managed cluster.
 - The LoclGP run directories created in this step will, upon completion, have their MonthlyInput directories populated with data selected according to the parameters set, and you're ready to run LocalGP.
