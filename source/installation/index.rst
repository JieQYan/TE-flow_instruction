Installation
============

This section describes the host requirements and setup steps needed to run
TE-flow as it is currently implemented in this repository.

TE-flow combines three dependency layers:

* host-level tools that must already be available on the machine
* Snakemake-managed conda environments under ``workflow/envs/``
* a Docker image used by the HiTE, RepeatMasker, and Juicer-related steps

.. toctree::
   :maxdepth: 1

   requirements
   install
