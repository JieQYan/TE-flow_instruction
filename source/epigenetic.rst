Epigenetic Module
=================

The ``epigenetic`` module processes BS-seq and ChIP-seq data in the genome and
TE annotation context produced by upstream modules. It supports read QC,
BS-seq methylation calling, TE/gene methylation integration, chromosome-window
methylation and density analysis, ChIP-seq histone peak calling, histone-DNA
methylation integration, optional expression-methylation analysis, and
epigenetic plots.

Before running this module, set the module switch in
``/path/to/workdir/config/config.yaml``:

.. code-block:: yaml

   run_epigenetic: true

Inputs
------

The module is driven by:

.. code-block:: text

   resources/epigenetic-sheet.csv

The current template uses:

.. code-block:: text

   species_id,sample_name,data_type,r1,r2

``species_id`` should match the species IDs used by assembly and annotation
outputs. ``sample_name`` is used directly in output paths. ``data_type``
selects the branch: use ``BS-seq`` for bisulfite sequencing and ``ChIP-seq``
for histone ChIP-seq samples.

BS-seq rows are treated as paired-end data and use both ``r1`` and ``r2``.
ChIP-seq rows are treated as single-end data and use ``r1``. The current
histone branch expects each ChIP sample to have a matching input-control row
named by appending ``_input`` to the ChIP sample name.

.. code-block:: text

   species_id,sample_name,data_type,r1,r2
   Ath,Ath_BS_rep1,BS-seq,/data/Ath_BS_rep1_R1.fq.gz,/data/Ath_BS_rep1_R2.fq.gz
   Ath,Ath_H3K27me3,ChIP-seq,/data/Ath_H3K27me3.fq.gz,
   Ath,Ath_H3K27me3_input,ChIP-seq,/data/Ath_H3K27me3_input.fq.gz,

The sample sheet and optional species filter are set in
``/path/to/workdir/config/config.yaml``:

.. code-block:: yaml

   params:
     epigenetic:
       epigenetic_sheet: "resources/epigenetic-sheet.csv"
       target_species: ""

If ``target_species`` is empty, all species in ``epigenetic-sheet.csv`` are
used. To analyze only selected species, use a comma-separated value such as
``"Ath,Mli"``.

Upstream Inputs
---------------

The epigenetic module uses:

.. code-block:: text

   results/assembly/final/{species}_Final.fa
   results/anno/standardized/{species}/{species}_standardized.out
   resources/refs/{species}.gene.gff3

BS-seq methylation and ChIP-seq mapping use the final assembly FASTA.
TE-aware methylation and histone integration depend on TE annotation outputs.
Gene density and metaplot steps use gene annotation files from
``resources/refs/`` when required by the corresponding scripts.

Rule Files
----------

When ``run_epigenetic: true`` is enabled, ``workflow/Snakefile`` uses these
rule files according to the data types present in ``epigenetic-sheet.csv``:

* ``workflow/rules/1_epigenetic_qc.smk``: runs fastp QC for BS-seq and
  ChIP-seq reads.
* ``workflow/rules/2_epigenetic_methylation.smk``: runs Bismark genome
  preparation, BS-seq mapping, methylation extraction, TE/gene methylation
  integration, chromosome-window methylation, per-TE methylation, and density
  analysis.
* ``workflow/rules/3_epigenetic_histone.smk``: runs Bowtie2 mapping,
  filtering, duplicate removal, MACS3 peak calling, and peak BED generation for
  ChIP-seq data.
* ``workflow/rules/5_epigenetic_histone_meth.smk``: integrates histone peaks
  with TE methylation summaries.
* ``workflow/rules/6_epigenetic_plot.smk``: generates methylation, histone,
  histone-methylation, and expression-methylation plots.
* ``workflow/rules/4_epigenetic_expr_meth.smk``: included only when
  ``run_expression: true`` is enabled in the same run.

Species whose Hi-C scaffolding is paused for manual correction are skipped by
downstream epigenetic target collection until ``out_JBAT.review.assembly`` or
``manual_ok`` is provided.

Command Pattern
---------------

Run the whole epigenetic module through the wrapper:

.. code-block:: bash

   python3 bin/TE-flow.py epigenetic \
     --workdir /path/to/workdir \
     --resources /path/to/workdir/resources \
     --cores 16

The wrapper reads ``/path/to/workdir/config/config.yaml`` when that file
exists, resolves ``resources/...`` paths through ``--resources``, and passes a
merged temporary config to Snakemake. When you run with a separate workdir,
prepare the ``config/`` and ``resources/`` directories under that workdir; see
:ref:`Working Directory and Resource Directory <working-directory-and-resource-directory>`.

Or run the whole epigenetic module directly with ``workflow/Snakefile``:

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

For expression-methylation cross analysis, enable expression in the same run:

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
       run_epigenetic=True run_expression=True

Read QC
-------

Run QC for all BS-seq and ChIP-seq rows:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until bsseq_qc chipseq_qc

Main outputs:

.. code-block:: text

   results/epigenetic/qc/BS-seq/{species}/{sample}.clean_R1.fastq.gz
   results/epigenetic/qc/BS-seq/{species}/{sample}.clean_R2.fastq.gz
   results/epigenetic/qc/ChIP-seq/{species}/{sample}.clean.fastq.gz
   results/epigenetic/qc/{BS-seq,ChIP-seq}/{species}/{sample}.fastp.html

QC parameters are controlled by:

.. code-block:: yaml

   params:
     epigenetic:
       qc:
         threads: 10
         bsseq:
           length_required: 30
           qualified_quality_phred: 15
           unqualified_percent_limit: 40
           disable_adapter_trimming: false
         chipseq:
           length_required: 20
           qualified_quality_phred: 15
           unqualified_percent_limit: 40
           disable_adapter_trimming: false

BS-seq Methylation Calling
--------------------------

Run Bismark genome preparation, mapping, and methylation extraction:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until bismark_methylation_extractor

Main outputs:

.. code-block:: text

   results/epigenetic/methylation/Mapping/{species}/{sample}_pe.bam
   results/epigenetic/methylation/Mapping/{species}/{sample}_pe.bedGraph.gz
   results/epigenetic/methylation/Mapping/{species}/{sample}_pe.CX_report.txt
   results/epigenetic/methylation/Mapping/{species}/{sample}_pe.bismark.cov.gz

Bismark parameters are controlled by:

.. code-block:: yaml

   params:
     epigenetic:
       methylation:
         enable: true
         bismark:
           build_threads: 8
           mapping_threads: 8
           extra_params: ""
           deduplicate: false

The current Bismark genome-preparation rule builds an index under:

.. code-block:: text

   results/epigenetic/methylation/Mapping/{species}/BismarkIndex/

Methylation Integration
-----------------------

Integrate methylation over genes, TEs, and per-TE bodies:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until integrate_methylation integrate_per_te_methylation

Main outputs:

.. code-block:: text

   results/epigenetic/methylation/meth_level/{species}/.integrate_methylation.done
   results/epigenetic/methylation/meth_level/{species}/{sample}_pe.cytosine.bed
   results/epigenetic/methylation/meth_level/{species}/{sample}_pe.metaplot.tsv
   results/epigenetic/methylation/per_te_meth/{species}/merged_perTE_body_methylation.tsv

The integration rules use the BS-seq methylation outputs, TE coordinates, and
gene coordinates. Samtools-related methylation thresholds are controlled by:

.. code-block:: yaml

   params:
     epigenetic:
       methylation:
         samtools:
           sort_threads: 8
           sort_extra_params: ""
           quality: 20
           coverage: 4
           regions: 600
           step: 50000

Chromosome Methylation and Density
----------------------------------

Run chromosome sliding-window methylation and gene/TE density analysis:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until integrate_chr_methylation integrate_density

Main outputs:

.. code-block:: text

   results/epigenetic/methylation/chr_meth/{species}/.integrate_chr_meth.done
   results/epigenetic/methylation/chr_meth/{species}/{species}.genome_500kb_100kb.bed
   results/epigenetic/methylation/chr_meth/{species}/{sample}_pe.chr_sw.methy.body.cg.txt
   results/epigenetic/methylation/density/{species}/chr_sw.genedensity.txt
   results/epigenetic/methylation/density/{species}/chr_sw.{family}_density.txt
   results/epigenetic/methylation/density/{species}/.integrate_density.flag

Window and density parameters are controlled by:

.. code-block:: yaml

   params:
     epigenetic:
       methylation:
         chr_sliding_window:
           window_size: 500000
           step_size: 100000
           target_te_family: null
         density:
           enable: true
           window_size: 500000
           step_size: 100000
           te_families: []

If ``te_families`` is empty, the current workflow selects the three TE families
with the largest total coverage for density tracks.

ChIP-seq Histone Peaks
----------------------

Run Bowtie2 mapping, filtering, duplicate removal, and MACS3 peak calling for
ChIP-seq samples with matching ``_input`` controls:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until generate_chipseq_peak_bed

Main outputs:

.. code-block:: text

   results/epigenetic/Histones/{species}/temp/{sample}.rmdup.bam
   results/epigenetic/Histones/{species}/generate_peak/{chip_sample}_peaks.bed
   results/epigenetic/Histones/{species}/generate_peak/{chip_sample}_peaks.broadPeak
   results/epigenetic/Histones/{species}/generate_peak/{chip_sample}_peaks.xls

The histone type is inferred from the ChIP sample name by matching keys under
``params.epigenetic.histone``. For example, a sample named
``Ath_H3K27me3`` matches the ``H3K27me3`` block. MACS3 uses the matching
histone-type block for ``broad``, ``qvalue``, and ``extra_opts``. Set
``broad: true`` for broad marks and ``broad: false`` for narrow marks according
to the actual histone modification. If your sample contains a histone type that
is not listed in ``config.yaml``, add a new block with the same modification
name that appears in ``sample_name``.

.. code-block:: yaml

   params:
     epigenetic:
       histone:
         species_genome_sizes:
           Ath: 139476048
         bowtie2:
           threads: 8
           extra_params: ""
         samtools:
           threads: 8
         filter:
           mapq: 30
         macs3:
           threads: 4
         H3K27me3:
           broad: true
           qvalue: 0.05
           extra_opts: ""
         H3K4me3:
           broad: false
           qvalue: 0.01
           extra_opts: ""

If ``species_genome_sizes`` does not provide a value for a species, the current
rule estimates genome size from ``results/assembly/final/{species}_Final.fa``.

Histone-Methylation Integration
-------------------------------

Integrate ChIP-seq histone peaks with TE methylation summaries:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until mark_chipseq_meth_done

Main outputs:

.. code-block:: text

   results/epigenetic/Histones/{species}/TE_peak_meth/TE_{chip_sample}_ratio_full.tsv
   results/epigenetic/Histones/{species}/TE_peak_meth/TE_{chip_sample}_epigenetic_summary.tsv
   results/epigenetic/Histones/{species}/.integrate_chipseq_meth.done

The integration step itself creates one summary for each non-input ChIP-seq
sample in ``epigenetic-sheet.csv``. The downstream histone-methylation plots
then use one summary file at a time. If ``target_mod_type`` is empty, the
plotting rule uses the first available ``TE_*_epigenetic_summary.tsv`` file for
that species; set ``target_mod_type`` when you want the plots to use a specific
modification such as ``H3K27me3``.

The current histone-methylation class plots divide TEs by CG methylation and
histone peak overlap. ``CG_mean > 0.5`` is treated as methylated, and
``overlap_ratio >= 0.2`` is treated as histone-marked. This gives four classes:
``DNA_methylation_only``, ``both``, ``H3K27me3_only``, and ``none``. The class
name still uses ``H3K27me3_only`` in the plotting scripts, so interpret it as
the selected histone mark when ``target_mod_type`` points to another
modification.

Histone-methylation plots can use a specific modification type:

.. code-block:: yaml

   params:
     epigenetic:
       histone_meth:
         target_mod_type: ""

Expression-Methylation Analysis
-------------------------------

Run TE expression rank versus DNA methylation analysis. The rule reads RNA-seq
sample names from ``rnaseq-sheet.csv`` and BS-seq sample names from
``epigenetic-sheet.csv`` for the same ``species_id``. The RNA-seq sample name
does not need to be the same as a BS-seq sample name; it only needs to be a
column in the expression TPM matrix, and the corresponding methylation files
need to exist for the BS-seq samples. When running through the main
``workflow/Snakefile``, keep ``run_expression: true`` so the expression-
methylation rule file is loaded; existing TPM files can be reused.

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
       run_epigenetic=True run_expression=True \
     --until mark_expr_meth_done

Main outputs:

.. code-block:: text

   results/epigenetic/methylation/expr_meth/{species}/{rna_sample}_TE_expr_rank.txt
   results/epigenetic/methylation/expr_meth/{species}/{rna_sample}_all_rank_metaplot.long.tsv
   results/epigenetic/methylation/expr_meth/{species}/{rna_sample}_TE_expr_rank_metaplot.mean.tsv
   results/epigenetic/methylation/expr_meth/{species}/.integrate_expr_meth.done

The expression-methylation branch combines:

.. code-block:: text

   results/expression/quantification/{species}/{species}_TE_TPM_matrix.txt
   results/epigenetic/methylation/meth_level/{species}/{species}.TE.bed
   results/epigenetic/methylation/meth_level/{species}/{bs_sample}_pe.cytosine.bed

Plotting
--------

Generate the main epigenetic plots:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until methylation_gene_te_plot methylation_chr_distribution_plot te_families_methylation_plot

Generate expression-methylation and histone-related plots when their upstream
outputs are available:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until te_expr_rank_methylation_plot te_histone_methylation_plot \
       te_epigenetic_length_group_plot te_epigenetic_family_composition_plot \
       te_histone_family_levels_plot

Plot outputs:

.. code-block:: text

   results/epigenetic/plot/{species}/meth/Gene_vs_TE_Methylation_Profiles.pdf
   results/epigenetic/plot/{species}/meth/Methylation_Gene_TE_Distribution.pdf
   results/epigenetic/plot/{species}/meth/TE_families_meth_level.pdf
   results/epigenetic/plot/{species}/expr_meth/{rna_sample}_TE_methylation_profiles_across_expression_ranks.pdf
   results/epigenetic/plot/{species}/hist_meth/DNA_Methylation_Across_TE_Epigenetic_States.pdf
   results/epigenetic/plot/{species}/hist_meth/Distribution_of_epigenetic_TE_classes_across_length_groups.pdf
   results/epigenetic/plot/{species}/hist_meth/Family_composition_within_TE_epigenetic_classes.pdf
   results/epigenetic/plot/{species}/hist/Average_{histone_type}_levels_across_TE_families.pdf

Practical Notes
---------------

* ``species_id`` in ``epigenetic-sheet.csv`` must match assembly, annotation,
  and optional expression outputs.
* ChIP-seq peak calling requires a matching ``{chip_sample}_input`` row for
  each ChIP sample.
* Histone sample names must contain a configured histone key such as
  ``H3K27me3`` or ``H3K4me3`` so the workflow can select MACS3 parameters.
* Expression-methylation analysis is intentionally requested only when
  ``run_expression`` and ``run_epigenetic`` are both enabled.
* ``--until`` still builds upstream dependencies needed for that stage.
