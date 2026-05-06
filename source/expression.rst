Expression Module
=================

The ``expression`` module processes paired-end RNA-seq data for TE expression
analysis. It runs read QC, prepares a species-level reference genome, builds a
HISAT2 index, maps RNA-seq reads, sorts and indexes BAM files, counts TE
features with featureCounts, builds count/TPM matrices, and writes a TE
expression heatmap.

Before running this module, set the module switch in
``/path/to/workdir/config/config.yaml``:

.. code-block:: yaml

   run_expression: true

Inputs
------

The module is driven by:

.. code-block:: text

   resources/rnaseq-sheet.csv

The current template uses:

.. code-block:: text

   species_id,sample_name,tissue,r1,r2,strandness

``species_id`` is used in paths such as
``results/expression/hisat2/{species}/`` and should match the assembly final
FASTA name ``results/assembly/final/{species}_Final.fa`` when
``genome_source: auto`` is used. ``sample_name`` is used in sample-level output
file names and becomes the sample column in the TPM matrix. The TE expression
heatmap uses those ``sample_name`` columns to distinguish samples; ``tissue`` is
metadata in the sample sheet and is not used as the heatmap column name by the
current plotting rule. ``r1`` and ``r2`` are the paired-end RNA-seq FASTQ files.

``strandness`` controls the HISAT2 ``--rna-strandness`` value for each sample.
Set it according to the RNA-seq library type: use ``RF`` for reverse-stranded
libraries such as common dUTP-style RNA-seq, and ``FR`` for forward-stranded
libraries. If this field is left empty, the current workflow uses ``RF``.

.. code-block:: text

   species_id,sample_name,tissue,r1,r2,strandness
   Ath,Col_0_flowers,flowers,/users/jieqyan/workspace/RNA_analysis/ref/raw/Col_0_flowers_1.fastq.gz,/users/jieqyan/workspace/RNA_analysis/ref/raw/Col_0_flowers_2.fastq.gz,RF
   Ath,Col_0_pollen,pollen,/users/jieqyan/workspace/RNA_analysis/ref/raw/Col_0_pollen_1.fastq.gz,/users/jieqyan/workspace/RNA_analysis/ref/raw/Col_0_pollen_2.fastq.gz,RF
   Ath,Col_0_rosettes,rosettes,/users/jieqyan/workspace/RNA_analysis/ref/raw/Col_0_rosettes_1.fastq.gz,/users/jieqyan/workspace/RNA_analysis/ref/raw/Col_0_rosettes_2.fastq.gz,RF
   Ath,Col_0_seedlings,seedlings,/users/jieqyan/workspace/RNA_analysis/ref/raw/Col_0_seedlings_1.fastq.gz,/users/jieqyan/workspace/RNA_analysis/ref/raw/Col_0_seedlings_2.fastq.gz,RF

The sample sheet path is set in ``/path/to/workdir/config/config.yaml``:

.. code-block:: yaml

   params:
     expression:
       rnaseq_sheet: "resources/rnaseq-sheet.csv"

Reference Genome
----------------

With the default ``genome_source: auto``, each species uses:

.. code-block:: text

   results/assembly/final/{species}_Final.fa

If you want expression analysis to use custom genome FASTA files, set
``genome_source: custom`` and provide one path per ``species_id``:

.. code-block:: yaml

   params:
     expression:
       genome_source: "custom"
       custom_genomes:
         Ath: "/path/to/Ath_genome.fa"
         Mli: "/path/to/Mli_genome.fa"

Rule Files
----------

When ``run_expression: true`` is enabled, ``workflow/Snakefile`` collects
expression targets under ``results/expression/`` and uses these rule files:

* ``workflow/rules/1_expression_hisat2.smk``: runs RNA-seq ``fastp`` QC,
  builds the HISAT2 index, maps reads, sorts BAM files, and indexes BAM files.
* ``workflow/rules/2_expression_quantification.smk``: selects the TE
  annotation input, converts TE annotation to SAF, runs featureCounts, builds
  count/TPM matrices, and plots TE expression.

Species listed in ``rnaseq-sheet.csv`` are filtered only when an upstream
manual Hi-C correction is still pending for that species. Otherwise each
species in the sheet is added to the expression targets.

Command Pattern
---------------

Run the whole expression module through the wrapper:

.. code-block:: bash

   python3 bin/TE-flow.py expression \
     --workdir /path/to/workdir \
     --resources /path/to/workdir/resources \
     --cores 16

The wrapper reads ``/path/to/workdir/config/config.yaml`` when that file
exists, resolves ``resources/...`` paths through ``--resources``, and passes a
merged temporary config to Snakemake. When you run with a separate workdir,
prepare the ``config/`` and ``resources/`` directories under that workdir; see
:ref:`Working Directory and Resource Directory <working-directory-and-resource-directory>`.

Or run the whole expression module directly with ``workflow/Snakefile``:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config \
       project_root=/path/to/TE-flow \
       resource_root=/path/to/workdir/resources

The module switches are normally read from ``config.yaml``. You can still
override them on the command line for a one-time expression-only run:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config \
       project_root=/path/to/TE-flow \
       resource_root=/path/to/workdir/resources \
       run_assembly=False run_annotation=False run_expression=True run_epigenetic=False

For one stage at a time, use Snakemake's ``--until`` option. This lets
Snakemake read ``rnaseq-sheet.csv`` and build targets for all eligible species
and samples.

RNA-seq QC
----------

Run fastp QC for all RNA-seq samples:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until rnaseq_qc_fastp

Main outputs:

.. code-block:: text

   results/expression/qc/{species}/{sample}_1_clean.fastq.gz
   results/expression/qc/{species}/{sample}_2_clean.fastq.gz
   results/expression/qc/{species}/{sample}.fastp.html
   results/expression/qc/{species}/{sample}.fastp.json

RNA-seq QC uses the shared ``params.qc.fastp`` block and the expression-specific
``qc_threads`` field:

.. code-block:: yaml

   params:
     qc:
       fastp:
         adapter_fasta: "auto"
         disable_adapter_trimming: false
         length_required: 50
         qualified_quality_phred: 20
         unqualified_percent_limit: 40
         trim_poly_g: true
         trim_poly_x: true
     expression:
       qc_threads: 10

HISAT2 Alignment
----------------

Build HISAT2 indexes for all species in the RNA-seq sheet:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until hisat2_build_index

Map reads and generate sorted, indexed BAM files:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until bam_index

Main outputs:

.. code-block:: text

   results/expression/hisat2/{species}/index/{species}_genome.1.ht2
   results/expression/hisat2/{species}/index/{species}_genome.8.ht2
   results/expression/hisat2/{species}/{sample}.bam
   results/expression/hisat2/{species}/{sample}.bam.bai

HISAT2 and samtools parameters are controlled by:

.. code-block:: yaml

   params:
     expression:
       hisat2:
         build_threads: 8
         build_extra_params: ""
         mapping_threads: 8
         mapping_extra_params: "--new-summary"
       samtools:
         sort_threads: 4
         sort_extra_params: ""

The current mapping rule gets ``--rna-strandness`` from the ``strandness``
column in ``rnaseq-sheet.csv``. If that column is empty for a sample, the
current ``workflow/Snakefile`` returns ``RF``.

TE Annotation for Quantification
--------------------------------

Generate the TE annotation table and SAF file used by featureCounts:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until generate_te_annotation te_annotation_to_saf

The quantification rule prefers:

.. code-block:: text

   results/anno/standardized/{species}/{species}_standardized.out

In the normal full workflow, this standardized file is the expression module's
input. During annotation standardization, if RepeatMasker normalization is not
available for a species, the annotation module can still write standardized
outputs from HiTE-derived results according to its fallback logic.

If you run expression without enabling annotation in the same Snakemake run
(``run_annotation: false``), the current expression rule checks for an existing
HiTE output and can use it directly when ``standardized.out`` is absent:

.. code-block:: text

   results/anno/hite/{species}/HiTE.out

Main outputs:

.. code-block:: text

   results/expression/quantification/{species}/{species}_TE_annotation.tsv
   results/expression/quantification/{species}/{species}_TE.saf

FeatureCounts Quantification
----------------------------

Run featureCounts for each RNA-seq sample:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until featurecounts_quantification

Main outputs:

.. code-block:: text

   results/expression/quantification/{species}/{sample}.count
   results/expression/quantification/{species}/{sample}.count.summary

featureCounts parameters are controlled by:

.. code-block:: yaml

   params:
     expression:
       quantification:
         threads: 4
         paired: true
         count_read_pairs: true
         multi_mapping: true
         multi_overlap: true
         fraction: true
         strandness: 0
         extra_params: ""

``strandness`` here is the featureCounts ``-s`` value: ``0`` means unstranded,
``1`` means forward-stranded, and ``2`` means reverse-stranded.

Count and TPM Matrices
----------------------

Merge sample-level counts and calculate TPM matrices for each species:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until generate_tpm_matrix

Main outputs:

.. code-block:: text

   results/expression/quantification/{species}/{species}_TE_count_matrix.txt
   results/expression/quantification/{species}/{species}_TE_TPM_matrix.txt

The TPM matrix is calculated from featureCounts output using TE length and
sample-level count columns. This stage does not have a separate config block in
the current rule file.

TE Expression Plot
------------------

Generate the TE expression heatmap:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until plot_te_expression

Main output:

.. code-block:: text

   results/expression/plot/{species}/{species}_TE_expression.pdf

The current plotting rule merges the TE annotation table with the TPM matrix,
sums expression by ``RepeatName`` and ``ClassFamily``, selects up to the top
100 TE entries with the largest variance across samples, and draws a heatmap.

Practical Notes
---------------

* ``species_id`` in ``rnaseq-sheet.csv`` must match the species IDs used by
  assembly and annotation outputs.
* With ``genome_source: auto``, run assembly first or provide
  ``results/assembly/final/{species}_Final.fa``.
* For TE-aware quantification, run annotation first or provide compatible
  ``results/anno/standardized/{species}/{species}_standardized.out`` or
  ``results/anno/hite/{species}/HiTE.out`` files.
* ``--until`` still builds upstream dependencies needed for that stage.
