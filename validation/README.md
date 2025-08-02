This project got its start as a handoff and generalization from Argo netCDF -> localGP ingestion scripts included in the original localGP matlab repo. We include here some notes and scripts on validation exercises performed to make sure this repo was making the same selections as the original localGP authors, before embarking on future iterations.

All scripts run in the pythonic environment described in provenance/environments/python-dev-env.txt.

## Argovis -> localGP validation

 - Downloaded a snapshot of Argo profiles as represented by Argovis in early July 2025
 - Ran argovis pipeline as recorded in release 'validation-prerelease'
 - Used `month_audit.py` to compare every profile selected by this pipeline to the list of profiles selected for a few months (Dec 2008, Oct-Dec 2020) by the original matlab selection code.
  - Match was very close, and absolutely all disjoint selections could be explained by one of a few well-understood reasons:
   - Argovis data was downloaded 6 months later than the snapshot the historical example we were comparing to was created; therefore, Argovis had more up to date QC information than the matlab run. Also, this results in some realtime mode files being absent and replaced with delayed mode files.
   - Argovis loses some data necessary for making identical choices to the original selection scripts:
    - Problematic APEX floats: Argovis doesn't persist pressure errors, and so can't antiselect these.
    - Out-of-order levels: Argovis sorts levels by pressure and thus can't antiselect for this.
    - Null pressures: Argovis suppresses any profile level without a meaningful pressure.
   - lat/long/timestamp cluster downsampling was not implemented for the argovis selection, resulting in 3 extra profiles in 2008/12; see more detailed discussion below.

## Argo netCDF -> localGP validation

 - Started from the January 2025 Argo snapshot: https://www.seanoe.org/data/00311/42182/#116315
 - Ran argonc pipeline as recorded in release 'validation-prerelease'
 - Used `month_audit.argonc.py` to compare every profile selected by this pipeline to the list of profiles selected for a few months by the original matlab selection code.
  - Match was exact for 2020/10 through 2020/12.
  - Exactly as the argovis case, in 2008/12 this pipeline accepted profiles ['4900845_107', '5900634_156', '4900845_105'] whereas the matlab selection did not; otherwise the match was exact.
   - Matlab selection throws out 2nd through nth profiles with identical lat/long/timestamp [here](https://github.com/argovis/localGP/blob/6f92c65f7d1a878717673ec9f645bec53ef76815/OHC_analysis-code-only/selectionAndVerticalIntegrationPchipTrapzInterpolation.m#L63-L76). This eliminates 5900634_156.
   - Matlab selection subsequently throws out groups of profiles with identical lat/lon and timestamps within 15 min [here](https://github.com/argovis/localGP/blob/6f92c65f7d1a878717673ec9f645bec53ef76815/OHC_analysis-code-only/selectionAndVerticalIntegrationPchipTrapzInterpolation.m#L78-L103), eliminating 4900845_105 and 4900845_107.
   - Pipeline code accepted these three profiles as it does not attempt to emulate this downsampling strategy (we plan a downsampling strategy based on profile clustering that will catch these cases, and smooth out localized oversampling).

