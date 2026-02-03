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

### Data sorting

After downloading the DOI of interest or rsyncing one of the GDACs, sort the profile netCDF files into folders organized by month:

 - The Argo DOI zips core and BGC profiles separately; at the time of writing, localgp-input only considers core profiles and assumes only the core archives are unzipped.
 - Sort handled by `sort_argonc.py`, see top of that file for usage instructions.
 - Slurm it with `sort_argonc.slurm` if desired; those who feel fancy could write a loop over DACs (aoml bodc csio incois kma meds coriolis csiro jma kordi nmdis), or even parallelize at the sub-DAC level (aoml takes forever).
 - Note this copies, and does not move, profile .nc, which means you'll need enough disk to accommodate.
 - Will create subdirectories `YYYY_MM` for each month of data under your target location.

### Processing pipeline

Once input netCDF files are sorted by month, `pipeline4localgp.sh` supports preparing these files for consumption by localGP:

 - Start by setting appropriate variables for this run in the block at the top of `pipeline4localgp.sh`.
 - Run `launch_localgp_pipelines.sh` to launch an appropriate pipeline of jobs for the study period on a slurm-managed cluster. Make sure to provide the appropriate paths to wherever you sorted your data in the previous step.
 - Each YYYY_MM directory will have an appropriately named .mat file representing the profiles for that month. Write a script to copy them into your target directory for localGP, `xx/MonthlyInputs/2004_2025/.`
