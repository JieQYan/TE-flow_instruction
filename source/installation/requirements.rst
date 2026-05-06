Requirements
============

TE-flow is designed for Linux-based systems with access to Snakemake, Conda or
Miniconda, and Docker.

Snakemake is used to execute workflow rules and manage dependencies. Module-
specific software environments are defined by the Conda environment files under
``workflow/envs/`` and are created automatically during workflow execution when
``--use-conda`` is enabled.

Docker is used for container-dependent TE annotation steps, especially HiTE- and
RepeatMasker-related components.

Required Runtime Commands
-------------------------

Before running TE-flow, the following commands should be available in the user
runtime environment:

* ``python3``
* ``snakemake``
* ``conda`` or ``mamba``
* ``docker``
* ``git``

If Snakemake, Conda, or Docker is not available on your system, please refer to
the official installation pages:

* `Snakemake installation <https://snakemake.readthedocs.io/en/stable/getting_started/installation.html>`_
* `Docker Engine installation <https://docs.docker.com/engine/install/>`_

Conda Environments
------------------

TE-flow does not require users to manually create separate environments for each
analysis module. Instead, module-specific environments are defined in
``workflow/envs/`` and are handled by Snakemake during workflow execution.

Common environment files include:

* ``assembly.yml``
* ``scaffolding.yml``
* ``hite.yml``
* ``standardize.yml``
* ``hisat2.yml``
* ``methylation.yml``
* ``chipseq.yml``
* ``plot.yml``

These environment files describe the software requirements for different rules
or modules. When ``--use-conda`` is enabled, Snakemake creates and reuses the
corresponding environments automatically.

Docker Usage
------------

Some TE-flow rules use Docker containers for TE annotation and standardization.
In the current implementation, Docker-dependent rules may call
``sudo docker ...`` directly.

If Docker requires ``sudo`` on your system, provide a runtime password file:

.. code-block:: text

   resources/secret.pass

This file is used only by Docker-dependent rules that require sudo access. If
Docker can be run without ``sudo`` in your environment, this file may not be
required.

Storage Requirements
--------------------

TE-flow can generate large intermediate files, especially during genome assembly,
Hi-C scaffolding, RNA-seq alignment, BS-seq methylation analysis, and ChIP-seq
processing.

Make sure the working directory has enough storage for:

* Conda environments created by Snakemake
* Docker images used by container-dependent rules
* temporary and intermediate files
* log files
* final results under ``results/``

For large genomes or multi-omics datasets, storage usage can increase rapidly.
It is recommended to place the work directory on a filesystem with sufficient
available space before running the workflow.