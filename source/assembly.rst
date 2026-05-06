Assembly Module
===============

The ``assembly`` module generates genome assemblies for downstream TE analysis.
It supports read preprocessing, genome-size estimation, HiFi-based primary
assembly, polishing, optional duplicate purging, optional Hi-C scaffolding,
assembly evaluation, and final FASTA generation.

The current implementation uses HiFi reads as the main input for de novo
assembly. Therefore, ``hifi_reads`` is required for samples that enter the main
assembly workflow.

Before running this module, set the module switch in
``/path/to/workdir/config/config.yaml``:

.. code-block:: yaml

   run_assembly: true

Inputs
------

The module is driven by:

.. code-block:: text

   resources/assembly-sheet.csv

The current template uses:

.. code-block:: text

   sample_id,hifi_reads,ont_reads,hic_r1,hic_r2,illumina_r1,illumina_r2

``sample_id`` becomes the wildcard used in output paths. If a sample does not
have one data type, leave that CSV field empty but keep the comma separators so
the column order stays unchanged.

.. code-block:: text

   sample_id,hifi_reads,ont_reads,hic_r1,hic_r2,illumina_r1,illumina_r2
   Ath,/data/Ath.hifi.fq.gz,,,,,
   Mli,/data/Mli.hifi.fq.gz,/data/Mli.ont.fq.gz,,,/data/Mli.R1.fq.gz,/data/Mli.R2.fq.gz
   Sp3,/data/Sp3.hifi.fq.gz,,/data/Sp3.hic.R1.fq.gz,/data/Sp3.hic.R2.fq.gz,,

The sample sheet path is set in ``/path/to/workdir/config/config.yaml``:

.. code-block:: yaml

   assembly_sheet: "resources/assembly-sheet.csv"

Rule Files
----------

When ``run_assembly: true`` is enabled, ``workflow/Snakefile`` collects
assembly targets under ``results/assembly/`` and uses these rule files:

* ``workflow/rules/1_assembly_qc.smk``: runs ``fastplong`` for HiFi/ONT reads
  and ``fastp`` for Illumina/Hi-C paired reads.
* ``workflow/rules/2_assembly_kmer.smk``: runs Jellyfish and GenomeScope.
  Illumina reads are preferred; HiFi is used when Illumina is absent.
* ``workflow/rules/3_assembly_main.smk``: runs Hifiasm with HiFi-only,
  HiFi+ONT, or HiFi+Hi-C inputs depending on the sample sheet and
  ``params.assembly.use_hic``.
* ``workflow/rules/4_assembly_polish_racon.smk``: runs iterative ONT and/or
  HiFi Racon polishing.
* ``workflow/rules/5_assembly_polish_illumina.smk``: runs NextPolish2 when
  Illumina polishing is enabled and both Illumina and HiFi reads are present.
* ``workflow/rules/6_assembly_purge_dups.smk``: maps Illumina reads to the
  best polished assembly, estimates cutoffs, and runs ``purge_haplotigs``.
* ``workflow/rules/7_assembly_scaffolding.smk``: maps Hi-C reads, runs YAHS,
  generates ``out_JBAT.hic``, and optionally applies manual Juicebox
  correction.
* ``workflow/rules/8_assembly_evaluate_qv.smk``: computes Yak QV from
  Illumina reads when available, otherwise from HiFi reads.
* ``workflow/rules/9_assembly_evaluate_busco_lai.smk``: runs BUSCO and LAI
  evaluation on the final assembly.
* ``workflow/rules/10_assembly_finalize.smk``: selects the best available
  assembly source and writes ``results/assembly/final/{sample_id}_Final.fa``.

Command Pattern
---------------

Run the whole assembly module through the wrapper:

.. code-block:: bash

   python3 bin/TE-flow.py assembly \
     --workdir /path/to/workdir \
     --resources /path/to/workdir/resources \
     --cores 16

The wrapper automatically reads ``/path/to/workdir/config/config.yaml`` when
that file exists, merges it with command-line options such as ``--workdir`` and
``--resources``, and passes the merged temporary config to Snakemake. Therefore
the wrapper command does not need a separate ``--configfile`` option. When you
run with a separate workdir, prepare the ``config/`` and ``resources/``
directories under that workdir; see
:ref:`Working Directory and Resource Directory <working-directory-and-resource-directory>`.

If you run directly inside the TE-flow project directory, you can instead edit
the project-local config and resource files. See
:ref:`Expected Runtime Inputs <expected-runtime-inputs>` and
:ref:`Configuration Template <configuration-template>` for the required file
layout and commonly edited fields.

Or run the whole assembly module directly with ``workflow/Snakefile``:

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
override them on the command line for a one-time run:

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
       run_assembly=True run_annotation=False run_expression=False run_epigenetic=False

For one stage at a time, use Snakemake's ``--until`` option. This lets
Snakemake read ``assembly-sheet.csv`` and build the relevant targets for all
eligible samples, instead of requiring you to name each output file manually.

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
     --until RULE_NAME

QC
--

Run QC for all available assembly reads:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until qc_fastplong qc_fastp_pe

This does not require every sample to contain every read type. The workflow
uses only the non-empty columns in ``assembly-sheet.csv``: ``qc_fastplong``
runs for rows with ``hifi_reads`` or ``ont_reads``, and ``qc_fastp_pe`` runs
for rows with complete ``illumina_r1``/``illumina_r2`` or
``hic_r1``/``hic_r2`` pairs. Missing optional data types are skipped. To run
only HiFi QC for one sample, target that report directly:

.. code-block:: bash

   snakemake results/assembly/qc/reports/Ath.hifi.fastplong.html \
     -s /path/to/TE-flow/workflow/Snakefile --use-conda \
     --directory /path/to/workdir --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources

QC parameters are set in ``/path/to/workdir/config/config.yaml``. The
``fastp`` block is used for Illumina and Hi-C paired-end reads, and the
``fastplong`` sub-block matching the read type is used for HiFi or ONT reads:

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
       fastplong:
         hifi:
           mean_qual: 15
           length_required: 1000
           length_limit: 0
           disable_adapter_trimming: false
         ont:
           mean_qual: 10
           length_required: 1000
           length_limit: 0
           disable_adapter_trimming: false

K-mer Analysis
--------------

Run K-mer counting and GenomeScope for all eligible samples:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until kmer_genomescope

The workflow targets Illumina GenomeScope output when Illumina reads exist and
HiFi GenomeScope output otherwise.

K-mer and GenomeScope parameters are controlled by:

.. code-block:: yaml

   params:
     kmer:
       kmer_size: 21
       jellyfish_mem: "20G"
       histo_high: 10000000
       genomescope_ploidy: 2
       genomescope_max_cov: 1000

Primary Assembly
----------------

Run QC, K-mer analysis, and Hifiasm for all samples with ``hifi_reads``:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 40 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until hifiasm_assembly

Hifiasm always requires ``hifi_reads``. It adds ``ont_reads`` automatically
when that column is filled. Hi-C assembly mode is used only when ``hic_r1`` and
``hic_r2`` are filled and ``use_hic: true`` is set in
``/path/to/workdir/config/config.yaml``. The default is ``use_hic: false``.

Hifiasm input mode and extra arguments are controlled by:

.. code-block:: yaml

   params:
     assembly:
       use_hic: false
       hifiasm_hifi_only: "--path-max 0.6"
       hifiasm_hifi_ont: "--ul-rate 0.15 --ul-tip 5 --path-max 0.5"
       hifiasm_hifi_hic: ""

Racon Polishing
---------------

Run Racon polishing for all eligible samples:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until racon_polish

The number of ONT and HiFi polishing rounds comes from ``racon_ont_rounds``
and ``racon_hifi_rounds`` in ``config.yaml``.

Racon and minimap2 polishing parameters are controlled by:

.. code-block:: yaml

   params:
     polish:
       racon_ont_rounds: 1
       racon_hifi_rounds: 1
       minimap2_ont_preset: "map-ont"
       minimap2_hifi_preset: "map-hifi"
       racon_window_length: 500
       racon_quality_threshold: 10.0
       racon_error_threshold: 0.3
       racon_extra_params: "-u"

Illumina Polishing
------------------

Run NextPolish2 for all samples where it is applicable:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until np_run_nextpolish_round1 np_run_nextpolish_roundN

This branch requires ``hifi_reads``, a complete
``illumina_r1``/``illumina_r2`` pair, and ``use_illumina_polish: true`` in
``/path/to/workdir/config/config.yaml``.

NextPolish2 and Yak parameters for Illumina polishing are controlled by:

.. code-block:: yaml

   params:
     polish:
       use_illumina_polish: true
       nextpolish_rounds: 1
       yak_kmer_sizes: "21,31"
       yak_bloom_filter_bits: 37
       minimap2_hifi_preset: "map-hifi"
       nextpolish_extra_params: ""

Purge Dups
----------

Run duplicate purging for all samples with HiFi and Illumina reads:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until pd_purge

The current purge-dups rules read the cutoff helper path from:

.. code-block:: yaml

   params:
     purge_dups:
       find_cutoff_script: "scripts/find_cutoff.py"

Changing ``find_cutoff_script`` changes the helper used to choose coverage
cutoffs. The ``bwa_threads`` and ``purge_threads`` fields in the template are
not read by the current purge-dups rule file, so changing them will not change
the thread count for this stage.

Hi-C Scaffolding
----------------

Run automatic YAHS scaffolding for all samples with HiFi and Hi-C reads:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until scaf_yahs

Generate Juicebox ``.hic`` files:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until scaf_juicer_pre

Manual correction is controlled by ``manual_correction`` in
``/path/to/workdir/config/config.yaml``.

If ``manual_correction: false``, TE-flow uses the YAHS result directly and
skips the manual Juicebox correction step.

If ``manual_correction: true``, TE-flow stops after generating Juicebox
inspection files in:

.. code-block:: text

   results/assembly/scaffolding/{sample_id}/

Open ``out_JBAT.hic`` and ``out_JBAT.assembly`` from that directory in local
Juicebox for manual review. If you edit the assembly, save the updated file as:

.. code-block:: text

   results/assembly/scaffolding/{sample_id}/out_JBAT.review.assembly

On the next run, TE-flow uses ``out_JBAT.review.assembly`` together with
``out_JBAT.liftover.agp`` to generate ``out_JBAT.FINAL.fa``.

If the automatic YAHS result does not need editing, create an empty
confirmation file instead:

.. code-block:: bash

   touch results/assembly/scaffolding/{sample_id}/manual_ok

After placing ``out_JBAT.review.assembly`` or creating ``manual_ok``, rerun the
assembly module. The workflow will detect the file and continue automatically:

.. code-block:: bash

   python3 bin/TE-flow.py assembly \
     --workdir /path/to/workdir \
     --resources /path/to/workdir/resources \
     --cores 16

Because transposable elements are dispersed repeats, assemblies for species
with high TE content may be more difficult to resolve in repeat-rich regions.
For those genomes, manual Hi-C correction is recommended to improve assembly
quality before downstream annotation.

Hi-C scaffolding parameters used by the current rules are:

.. code-block:: yaml

   params:
     scaffolding:
       juicer_jar_path: "/opt/juicer-1.6/CPU/common/juicer_tools.1.9.9_jcuda.0.8.jar"
       juicer_tools_docker_image: "teflow/te-flow:1.0"
       manual_correction: false
       juicer_executable: "juicer"
     annotation:
       hite:
         sudo_password_file: "resources/secret.pass"

``sudo_password_file`` is used only by the Juicebox ``.hic`` generation step,
where the rule runs Docker with ``sudo`` to call Juicer tools. Set it to a file
that contains the sudo password for the runtime machine, for example
``resources/secret.pass``. If Docker can run without sudo in your environment,
this file may not be needed by that step.

Evaluation
----------

Run Yak QV for all assembled samples:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until yak_qv

Yak QV parameters are controlled by:

.. code-block:: yaml

   params:
     evaluation:
       yak:
         k_illumina: 21
         k_hifi: 31
         threads: 20

The QV report is written to:

.. code-block:: text

   results/assembly/evaluate/QV/{sample_id}/yak_qv.txt

Use ``less +G`` to jump to the final summary lines:

.. code-block:: bash

   less +G results/assembly/evaluate/QV/Ath/yak_qv.txt

The report header includes:

.. code-block:: text

   CC      CT  kmer_occurrence    short_read_kmer_count  raw_input_kmer_count  adjusted_input_kmer_count
   CC      FR  fpr_lower_bound    fpr_upper_bound
   CC      ER  total_input_kmers  adjusted_error_kmers
   CC      CV  coverage
   CC      QV  raw_quality_value  adjusted_quality_value

Use the adjusted value in the final ``QV`` line as the assembly QV. For
example, in ``QV 58.884 56.443``, the final QV is ``56.443``; ``58.884`` is
the raw value before Yak's adjustment.

Run BUSCO:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until run_busco

BUSCO parameters are controlled by:

.. code-block:: yaml

   params:
     evaluation:
       busco:
         lineage: "brassicales_odb12"
         mode: "geno"

Change ``lineage`` according to the assembled species. See
:ref:`Configuration Template <configuration-template>` for the BUSCO lineage
dataset link. BUSCO text summaries are written as ``.txt`` files under:

.. code-block:: text

   results/assembly/evaluate/busco/{sample_id}/

Run LAI:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until lai_retriever

LAI uses the configured ``LTR_FINDER_parallel`` executable path:

.. code-block:: yaml

   params:
     evaluation:
       lai:
         ltr_finder_parallel_path: "LTR_FINDER_parallel"

The LAI result is written to:

.. code-block:: text

   results/assembly/evaluate/LAI/{sample_id}/{sample_id}.out.LAI

Final Assembly
--------------

Generate final standardized assemblies for all samples with HiFi reads:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until finalize_output

Finalization selects the best available upstream source in this general order:
manual Hi-C correction, automatic YAHS scaffolding, purge-dups output,
polished assembly, then direct Hifiasm contigs. If
``resources/refs/{sample_id}.fa`` exists, finalization can use it to help
rename chromosome IDs before writing ``results/assembly/final/{sample_id}_Final.fa``.
Before providing ``resources/refs/{sample_id}.fa``, strongly standardize the
chromosome names first so downstream annotation and visualization use stable
IDs. See :ref:`Reference Files <reference-files>` for the expected naming
details.

Practical Notes
---------------

* ``--until`` still builds upstream dependencies needed for that stage.
* Branches are data-dependent. Samples without Illumina reads skip
  NextPolish2 and purge-dups; samples without Hi-C reads skip scaffolding.
* To run one exact output instead of a whole stage, replace ``--until ...``
  with the target path you want, such as
  ``results/assembly/final/Ath_Final.fa``.
* In manual Hi-C correction mode, downstream final/evaluation targets may wait
  until ``out_JBAT.review.assembly`` or ``manual_ok`` is provided.
