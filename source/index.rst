.. TE-flow documentation master file.

TE-flow Documentation
=====================

TE-flow is a Snakemake-based workflow for transposable element (TE) analysis in
eukaryotic genomes. It organizes genome assembly, TE annotation, expression
profiling, and epigenetic analysis into a project-oriented pipeline. The
workflow can be launched from a user-defined work directory while keeping the
codebase, runtime outputs, and reusable resources separate.

Overview
--------

TE-flow currently provides four major modules:

* ``assembly``: de novo genome assembly for producing evaluated genome
  assemblies from long-read, short-read, and Hi-C data

* ``anno``: TE annotation and characterization for generating standardized TE
  annotations and genome-wide TE summaries

* ``expression``: TE expression profiling for quantifying TE expression from
  RNA-seq data

* ``epigenetic``: TE-centered epigenetic profiling for integrating DNA
  methylation, histone modification, TE annotation, and expression information

The workflow is implemented using:

* ``bin/TE-flow.py`` as the command-line entry point
* ``workflow/Snakefile`` as the main Snakemake workflow
* ``workflow/rules/`` for modular rule definitions
* ``config/config.yaml`` as the main configuration template
* ``scripts/`` for helper scripts, format conversion, and plotting

Key Features
------------

* Run assembly, annotation, expression, and epigenetic modules with
  ``TE-flow.py`` subcommands

* Track workflow dependencies and outputs automatically with Snakemake

* Use Docker-supported HiTE and RepeatMasker components for TE annotation and
  standardization

* Extend TE results with optional analyses including TEsorter, phylogeny,
  collinearity, chromosome distribution, and Circos visualization

* Keep project files, runtime outputs, and reusable resources in separate
  directories

* Collect species-specific targets and generate downstream plots automatically

Workflow Modules
----------------

Genome Assembly
~~~~~~~~~~~~~~~

The ``assembly`` module processes long-read, short-read, and Hi-C sequencing
data to generate chromosome-level or scaffold-level genome assemblies. It
supports read quality control, K-mer analysis, primary assembly, polishing,
duplicate purging, Hi-C scaffolding, and assembly quality assessment.

Main tools include ``fastp``, ``fastplong``, ``jellyfish``, ``GenomeScope``,
``hifiasm``, ``minimap2``, ``racon``, ``NextPolish2``, ``purge_dups``,
``YAHS``, ``Juicer``, ``Yak``, ``BUSCO``, and LAI-related tools.

Typical outputs include cleaned reads, K-mer profiling results, polished genome
assemblies, purged assemblies, Hi-C scaffolding files, QV estimates, BUSCO
results, LAI results, and the final genome FASTA.

TE Annotation and Characterization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``anno`` module performs TE annotation, standardization, classification,
and genome-wide TE visualization. It uses HiTE for TE discovery and
RepeatMasker for annotation standardization, followed by downstream TE
characterization.

Main analyses include TE annotation, standardized ``.out`` and ``.gff`` output
generation, TE family statistics, chromosome-level TE distribution, TEsorter
classification, LTR phylogeny, collinearity analysis, and Circos
visualization.

Typical outputs include standardized TE annotations, TE family summaries,
Kimura divergence landscapes, chromosome distribution plots, phylogenetic tree
files, synteny anchors, and Circos figures.

Expression Profiling
~~~~~~~~~~~~~~~~~~~~

The ``expression`` module processes RNA-seq data and estimates TE expression
levels using the genome assembly and TE annotation results. It supports RNA-seq
quality control, genome alignment, TE-level quantification, TPM matrix
generation, and expression visualization.

Main tools include ``fastp``, ``HISAT2``, ``samtools``, ``featureCounts``,
``Rscript``, and downstream plotting tools.

Typical outputs include cleaned RNA-seq reads, aligned BAM files, TE count
matrices, TE TPM matrices, and TE expression heatmaps.

Epigenetic Profiling
~~~~~~~~~~~~~~~~~~~~

The ``epigenetic`` module analyzes BS-seq and ChIP-seq data in a TE-centered
framework. It integrates methylation profiles, histone modification signals, TE
annotations, and TE expression results for downstream epigenetic
visualization.

Main analyses include BS-seq quality control, Bismark-based methylation
calling, feature-level methylation profiling, chromosome-scale methylation
summaries, ChIP-seq alignment and peak analysis, expression-methylation
integration, and histone-methylation integration.

Typical outputs include cytosine methylation tables, gene and TE methylation
profiles, chromosome methylation and density plots, TE family methylation
summaries, expression-rank methylation profiles, TE epigenetic state
summaries, and histone modification plots.

Quick Start
-----------

Run a module through the TE-flow command-line wrapper:

.. code-block:: bash

   python3 bin/TE-flow.py assembly --workdir /path/to/workdir --cores 16
   python3 bin/TE-flow.py anno --workdir /path/to/workdir --resources /path/to/resources --cores 16
   python3 bin/TE-flow.py expression --workdir /path/to/workdir --resources /path/to/resources --cores 16
   python3 bin/TE-flow.py epigenetic --workdir /path/to/workdir --resources /path/to/resources --cores 16

The wrapper invokes Snakemake with ``--use-conda`` internally, so conda
environments defined in ``workflow/envs/`` can be created automatically during
execution.

Alternatively, run the workflow directly with Snakemake:

.. code-block:: bash

   snakemake \
     -s workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config \
       project_root=/path/to/TE-flow \
       resource_root=/path/to/resources

Project Layout
--------------

The repository is organized as follows:

.. code-block:: text

   TE-flow/
   |-- bin/                  command-line entry points
   |-- config/               default configuration templates
   |-- docker/               container build definitions
   |-- resources/            example or shared resources
   |-- scripts/              helper and plotting scripts
   |-- workflow/
   |   |-- Snakefile         main workflow entry
   |   |-- envs/             conda environments
   |   `-- rules/            modular rule files
   `-- README_TE-flow.md     project-level usage notes

.. _expected-runtime-inputs:

Expected Runtime Inputs
-----------------------

TE-flow expects sample sheets and reference files to be available in the
configured work or resource directory.

Assembly Sample Sheet
~~~~~~~~~~~~~~~~~~~~~

``resources/assembly-sheet.csv`` describes assembly-related sequencing data.
The current template uses the following columns:

.. code-block:: text

   sample_id,hifi_reads,ont_reads,hic_r1,hic_r2,illumina_r1,illumina_r2

``sample_id`` is used as the species or assembly identifier in downstream file
names.

RNA-seq Sample Sheet
~~~~~~~~~~~~~~~~~~~~

``resources/rnaseq-sheet.csv`` describes RNA-seq samples. The current template
uses the following columns:

.. code-block:: text

   species_id,sample_name,tissue,r1,r2,strandness

``species_id`` should match the corresponding assembly or annotation
identifier. ``sample_name`` is used in expression and
expression-methylation-related output files.

Epigenetic Sample Sheet
~~~~~~~~~~~~~~~~~~~~~~~

``resources/epigenetic-sheet.csv`` describes BS-seq and ChIP-seq samples. The
current template uses the following columns:

.. code-block:: text

   species_id,sample_name,data_type,r1,r2

``data_type`` distinguishes inputs such as ``BS-seq`` and ``ChIP-seq``.
``sample_name`` is also used to infer histone-mark-specific analyses, for
example ``Col_0_H3K27me3`` and ``Col_0_H3K27me3_input``.

.. _reference-files:

Reference Files
~~~~~~~~~~~~~~~

Reference files are placed under ``resources/refs/`` when chromosome-level
plots, collinearity analysis, or genome-guided finalization are required. The
current workflow expects species-based names such as:

.. code-block:: text

   {species}.fa
   {species}.gene.gff3

TE-flow includes automatic handling for some chromosome-name inconsistencies
between the reference FASTA and GFF3 annotation. However, inconsistent
chromosome names may still interrupt downstream analysis or create coordinate
conflicts.

Before running the workflow, users are strongly advised to standardize
chromosome identifiers in both files. A practical convention is to use
``Chr0X``-style names such as ``Chr01``, ``Chr02``, and ``Chr03`` for numbered
chromosomes, and consistent labels such as ``ChrX`` or ``ChrY`` when
applicable. Chromosome names should be identical between ``{species}.fa`` and
``{species}.gene.gff3``.

Docker Password File
~~~~~~~~~~~~~~~~~~~~

``resources/secret.pass`` is required only when Docker-dependent rules need
``sudo`` access. This file stores the sudo password used by container-dependent
steps such as HiTE and RepeatMasker-related rules.

Outputs
-------

By default, TE-flow writes runtime outputs under the user work directory. The
main output directories are:

* ``results/assembly/``
* ``results/anno/``
* ``results/expression/``
* ``results/epigenetic/``
* ``logs/``

Navigation
----------

.. toctree::
   :maxdepth: 2
   :caption: Contents

   installation/index
   assembly
   anno
   expression
   epigenetic
   example_data
