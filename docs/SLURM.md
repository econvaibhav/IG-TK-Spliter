# Legacy entry points and Slurm arrays

| Script | Behavior |
| --- | --- |
| `main.py` | Processes a hard-coded list of seven Finland recordings. Its folder parameter is not used for discovery. |
| `main_array_generate.py` | Walks a hard-coded Spain directory and writes a JSON list to `Spain.txt`. |
| `main_array.py` | Reads `Spain.txt` and selects `SLURM_ARRAY_TASK_ID - 1`. |

All three scripts execute work at top level when imported. Read their path
configuration before executing them. They dispatch on the exact platform
folder names `Instagram` and `Tiktok`.

## Array indexing

For a list of N recordings, task IDs are 1 through N. A missing variable fails
during integer conversion. The existing code checks only the upper bound;
task ID zero becomes Python index `-1` and can select the last recording.

The manifest generator neither sorts discovery nor filters file extensions.
It skips paths whose immediate grandparent is exactly `Others`. Use the same
manifest throughout a job array so the index mapping stays consistent.

## Input handling

The shared processor removes its input pathname after the final export.
These legacy entry points pass their configured paths directly. Use disposable
copies for this workflow; do not point them at the only copy of a recording.
Cluster-specific partitions, accounts and resource allocations belong in the
job configuration for your CSC environment.
