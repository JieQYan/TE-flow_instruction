Annotation Module
=================

The ``anno`` module generates transposable element annotations for downstream
TE analysis. It starts from assembled genomes, runs HiTE-based de novo TE
annotation, optionally normalizes TE names with RepeatMasker / Dfam, writes a
standardized annotation layer, and then runs optional TE classification,
chromosome distribution, phylogeny, collinearity, and Circos analyses.

By default, annotation uses the final assembly produced by the assembly module:

.. code-block:: text

   results/assembly/final/{species}_Final.fa

Before running this module, set the module switch in
``/path/to/workdir/config/config.yaml``:

.. code-block:: yaml

   run_annotation: true

If the final assembly files have not been generated yet, run the assembly
module first or also set ``run_assembly: true`` in ``config.yaml`` so Snakemake
can build the upstream assembly targets.

Inputs
------

The annotation species list is usually read from ``assembly_sheet`` in
``/path/to/workdir/config/config.yaml``. Samples with a filled ``hifi_reads``
column are used as annotation species because they are expected to have final
assembly outputs.

The default assembly sheet is:

.. code-block:: text

   resources/assembly-sheet.csv

The current template uses:

.. code-block:: text

   sample_id,hifi_reads,ont_reads,hic_r1,hic_r2,illumina_r1,illumina_r2

``sample_id`` becomes the ``{species}`` wildcard in annotation paths. For
example, ``Ath`` uses the upstream assembly file:

.. code-block:: text

   results/assembly/final/Ath_Final.fa

and writes annotation outputs such as:

.. code-block:: text

   results/anno/hite/Ath/
   results/anno/standardized/Ath/Ath_standardized.out

If you want to run annotation from custom genome FASTA files instead of
``results/assembly/final/{species}_Final.fa``, pass them through the wrapper
with ``--genome``.

Species Selection and Pairwise Behavior
---------------------------------------

Most annotation submodules first build an annotation species list. In normal
use, you do not need to write this list manually. TE-flow reads
``assembly_sheet`` from ``/path/to/workdir/config/config.yaml`` and uses the
``sample_id`` values whose ``hifi_reads`` field is non-empty. These sample IDs
become the annotation species IDs used in paths such as
``results/anno/hite/{species}/`` and ``results/anno/standardized/{species}/``.

There is also an advanced override supported by the workflow code:
``params.annotation.hite.species_list``. This field is not included in the
default ``config.yaml`` template, so most users can ignore it. If you add it
manually, it should be paired with explicit genome inputs; otherwise the
default ``assembly_sheet``-based selection is clearer and safer.

Example:

.. code-block:: yaml

   params:
     annotation:
       hite:
         species_list: ["Ath", "Mli"]
         genomes:
           - "/path/to/Ath_Final.fa"
           - "/path/to/Mli_Final.fa"

In this mode, each value in ``species_list`` is matched to the genome at the
same position in ``genomes``.

Single-species rules are run once per selected species. Comparative outputs
are generated only when at least two selected species are available:

* ``workflow/rules/4_annotation_visualize.smk`` writes per-species summary
  plots and, when two or more species are present, also writes combined
  cross-species summary plots such as combined TE family abundance, genomic
  occupancy, identity, and Kimura landscape figures.
* ``workflow/rules/7_annotation_phylogeny.smk`` collects top LTR families
  across the selected species, extracts RT-domain sequences per species, then
  merges the same family from all species into
  ``results/anno/iqtree/All_Species.{family}.RT.fa`` before MAFFT and IQ-TREE.
* ``workflow/rules/8_annotation_collinearity.smk`` runs intraspecific
  collinearity for each species when ``intraspecific: true`` and all pairwise
  interspecific combinations when ``interspecific: true``.
* ``workflow/rules/9_annotation_circos.smk`` draws one species pair. The
  searchable config field is ``species_pair`` under
  ``params: annotation: circos:``. If ``species_pair`` is empty, the workflow
  uses the first two annotation-ready species.

Rule Files
----------

When ``run_annotation: true`` is enabled, ``workflow/Snakefile`` collects
annotation targets under ``results/anno/`` and uses these rule files:

* ``workflow/rules/1_annotation_hite.smk``: runs HiTE in Docker, writes the
  consensus TE library, HiTE ``.out`` / ``.gff`` files, chromosome name map, and
  intact LTR files under ``results/anno/hite/{species}/``.
* ``workflow/rules/2_annotation_repeatmasker.smk``: exports a species-specific
  Dfam library with ``famdb.py`` and runs RepeatMasker on the HiTE TE library
  when ``repeatmasker.enable`` is true and the species exists in
  ``species_map``.
* ``workflow/rules/3_annotation_standardize.smk``: writes stable downstream
  files under ``results/anno/standardized/{species}/``. If RepeatMasker is not
  available for a species, it falls back to filtered HiTE outputs.
* ``workflow/rules/4_annotation_visualize.smk``: builds FASTA indexes and plots
  TE classification, abundance, identity, Kimura divergence, LTR insertion time,
  and chromosome distribution figures.
* ``workflow/rules/5_annotation_tesorter.smk``: classifies intact LTR sequences
  with TEsorter and writes ``.cls`` and ``.dom`` outputs.
* ``workflow/rules/6_annotation_te_chromosome.smk``: builds chromosome windows,
  calculates gene density, calculates TE family density, and writes
  ``results/anno/TE_chr/{species}/te_chr_analysis.done``.
* ``workflow/rules/7_annotation_phylogeny.smk``: selects top LTR families,
  extracts RT-domain sequences, runs MAFFT and IQ-TREE, and writes
  ``results/anno/iqtree/phylogeny.done``.
* ``workflow/rules/8_annotation_collinearity.smk``: prepares CDS / BED files and
  runs intra- and interspecific JCVI collinearity analysis.
* ``workflow/rules/9_annotation_circos.smk``: prepares Circos data and writes
  species-pair Circos plots under ``results/anno/plot/``.

Command Pattern
---------------

Run the whole annotation module through the wrapper:

.. code-block:: bash

   python3 bin/TE-flow.py anno \
     --workdir /path/to/workdir \
     --resources /path/to/workdir/resources \
     --cores 16

Run annotation with explicit genome files:

.. code-block:: bash

   python3 bin/TE-flow.py anno \
     --workdir /path/to/workdir \
     --resources /path/to/workdir/resources \
     --cores 16 \
     --genome /path/to/Ath_Final.fa /path/to/Mli_Final.fa

Run the whole annotation module directly with ``workflow/Snakefile``:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources

The module switches are normally read from ``config.yaml``.

You can still override module switches on the command line for a one-time run:

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
       run_assembly=False run_annotation=True run_expression=False run_epigenetic=False

For one annotation stage at a time, use Snakemake's ``--until`` option. This
lets Snakemake read the species list and build the relevant targets for all
eligible species, instead of requiring you to name each species output manually.

HiTE Annotation
---------------

Run HiTE for all annotation species:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until run_hite_docker

Main outputs:

.. code-block:: text

   results/anno/hite/{species}/confident_TE.cons.fa
   results/anno/hite/{species}/HiTE.out
   results/anno/hite/{species}/HiTE.full_length.gff
   results/anno/hite/{species}/HiTE.gff
   results/anno/hite/{species}/chr_name.map
   results/anno/hite/{species}/intact_LTR.list
   results/anno/hite/{species}/intact_LTR.fa

The Docker image, thread count, password file, and extra HiTE parameters are
set in ``/path/to/workdir/config/config.yaml``:

.. code-block:: yaml

   params:
     annotation:
       hite:
         image: "teflow/te-flow:1.0"
         threads: 20
         sudo_password_file: "resources/secret.pass"
         extra_params: ""

RepeatMasker Normalization
--------------------------

Run RepeatMasker normalization for species listed in ``species_map``:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until run_repeatmasker

RepeatMasker is controlled in ``/path/to/workdir/config/config.yaml``:

.. code-block:: yaml

   params:
     annotation:
       repeatmasker:
         enable: true
         docker_image: "teflow/te-flow:1.0"
         threads: 15
         independent_visualization: false
         species_map:
           Ath: "Arabidopsis thaliana"
           Mli: "Meniocus linifolius"

Update ``species_map`` so each sample ID maps to the Dfam species name that
RepeatMasker should use.

Standardized Annotation
-----------------------

Generate standardized annotation files for all annotation species:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until standardize_te_annotation

Main outputs:

.. code-block:: text

   results/anno/standardized/{species}/{species}_standardized.out
   results/anno/standardized/{species}/{species}_standardized.full_length.gff

Downstream expression and epigenetic modules use these standardized files when
they are available, so this is the most important checkpoint after HiTE and
RepeatMasker.

Standardization uses the RepeatMasker settings described above; it does not
have a separate config block. In ``workflow/rules/3_annotation_standardize.smk``,
species with usable RepeatMasker output are standardized against that
RepeatMasker result. Species without usable RepeatMasker output are written as
filtered HiTE-derived standardized files, so downstream rules can still read
the same ``results/anno/standardized/{species}/`` interface.

For paired or combined visualizations, ``independent_visualization: false`` is
the conservative mode: treat the selected species as one comparison set and
use RepeatMasker-derived standardized annotations only when all species in that
set have successful Dfam / RepeatMasker normalization. If you set
``independent_visualization: true``, each species can be considered
independently, so mixed RepeatMasker-derived and HiTE-derived standardized
annotations may appear in the same downstream comparison.

TE Visualization
----------------

Generate the core TE summary plots. This stage creates per-species plots and,
when at least two annotation species are available, also creates combined
cross-species plots:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until visualize_all_te_statistics plot_kimura_landscape_all

Representative outputs:

.. code-block:: text

   results/anno/plot/{species}/{species}_Distribution_of_TE_Classifications_pie.pdf
   results/anno/plot/{species}/{species}_Cumulative_Length_of_TE_Families.pdf
   results/anno/plot/{species}/{species}_Numerical_Abundance_of_Intact_TE_Families.pdf
   results/anno/plot/{species}/{species}_identity_values.pdf
   results/anno/plot/{species}/{species}_Kimura_divergence_landscape_of_TE.pdf
   results/anno/plot/Cumulative_Length_of_TE_Families.pdf
   results/anno/plot/Genomic_Occupancy_of_TE_Families.pdf
   results/anno/plot/Numerical_Abundance_of_Intact_TE_Families.pdf
   results/anno/plot/identity_values.pdf
   results/anno/plot/Kimura_divergence_landscape_of_TE.pdf

``visualize_all_te_statistics`` produces both per-species plots and combined
plots when there are at least two species. ``plot_kimura_landscape_all``
similarly writes one Kimura landscape per species and one combined Kimura
landscape across all selected species. ``plot_ltr_insertion_time`` writes one
combined insertion-time plot from all selected species after TEsorter has
finished.

TEsorter
--------

Run TEsorter for all species with HiTE intact LTR outputs:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until run_tesorter

Main outputs:

.. code-block:: text

   results/anno/TEsorter/{species}/{species}_TEsorter.cls.tsv
   results/anno/TEsorter/{species}/{species}_TEsorter.cls.lib
   results/anno/TEsorter/{species}/{species}_TEsorter.cls.pep
   results/anno/TEsorter/{species}/{species}_TEsorter.dom.tsv
   results/anno/TEsorter/{species}/{species}_TEsorter.dom.faa

TEsorter is controlled in ``/path/to/workdir/config/config.yaml``:

.. code-block:: yaml

   params:
     annotation:
       tesorter:
         enable: true
         database: "rexdb-plant"
         threads: 24
         extra_params: ""
         mutation_rate: 7e-9

Set ``mutation_rate`` according to the species being annotated before using
LTR insertion-time plots. The default ``7e-9`` is commonly used for many plant
analyses, but it should be replaced when a better species-specific mutation
rate is available.

Generate the LTR insertion time plot after TEsorter:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until plot_ltr_insertion_time

Output:

.. code-block:: text

   results/anno/plot/LTR_insertion_time.pdf

TE Chromosome Distribution
--------------------------

Run TE and gene density analysis on chromosome windows:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until aggregate_te_chromosome_analysis plot_chromosome_distribution

Main outputs:

.. code-block:: text

   results/anno/TE_chr/{species}/chr_sw.bed6
   results/anno/TE_chr/{species}/gene_density.txt
   results/anno/TE_chr/{species}/chr_sw.{family}.density.txt
   results/anno/TE_chr/{species}/te_chr_analysis.done
   results/anno/plot/{species}/{species}_Chromosomal_Distribution_of_Genes_and_TEs.pdf

The gene GFF directory is set in ``/path/to/workdir/config/config.yaml``:

.. code-block:: yaml

   params:
     annotation:
       te_chromosome:
         enable: true
         window_size: 1000000
         window_step: 200000
         te_chr_families: 5
         gene_gff_dir: "resources/refs"

``workflow/rules/6_annotation_te_chromosome.smk`` ranks TE families from
``results/anno/hite/{species}/HiTE.full_length.gff`` by abundance. By default,
``te_chr_families: 5`` selects the five most abundant TE families for each
species and calculates a separate density file for each selected family. Set
``te_chr_families: "all"`` if you want density files for every TE family.

Gene annotation files should be named by species ID, for example:

.. code-block:: text

   resources/refs/Ath.gene.gff3
   resources/refs/Mli.gene.gff3

LTR Phylogeny
-------------

Run LTR family selection, sequence extraction, MAFFT alignment, and IQ-TREE.
This module is cross-species by design: it selects the top LTR families across
all selected annotation species, extracts RT-domain sequences per species, then
merges the same family from all species before building the tree. This makes it
easier to compare how the same TE family evolved across species.

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until phylogeny_complete

Main outputs:

.. code-block:: text

   results/anno/iqtree/top_families.txt
   results/anno/iqtree/All_Species.{family}.RT.fa
   results/anno/iqtree/{family}.RT.aln
   results/anno/iqtree/{family}.iqtree.treefile
   results/anno/iqtree/phylogeny.done

Phylogeny parameters are set in ``/path/to/workdir/config/config.yaml``:

.. code-block:: yaml

   params:
     annotation:
       phylogeny:
         enable: true
         top_families: 2
         mafft_threads: 4
         mafft_algorithm: "auto"
         iqtree_threads: 4
         iqtree_bootstrap: 1000
         iqtree_model: "AUTO"

Collinearity
------------

Run CDS / BED preparation and JCVI collinearity analysis. By default,
``intraspecific: true`` runs each selected species against itself, and
``interspecific: true`` runs every pairwise combination of selected species:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until all_collinearity

Main outputs:

.. code-block:: text

   results/anno/collinearity/prep/{species}.cds
   results/anno/collinearity/prep/{species}.bed
   results/anno/collinearity/{species}/{species}.collinearity.done
   results/anno/collinearity/{species1}_vs_{species2}.collinearity.done
   results/anno/collinearity/all_collinearity.done

Collinearity uses gene GFF files from ``gene_gff_dir``:

.. code-block:: yaml

   params:
     annotation:
       collinearity:
         enable: true
         intraspecific: true
         interspecific: true
         gene_gff_dir: "resources/refs"
         blast_evalue: 1e-5
         blast_threads: 8
         cscore: 0.99
         min_size: 5
         max_size: 100
         generate_plots: false
         plot_dpi: 300
         plot_format: "pdf"

Pairwise Plotting
-----------------

Cross-species annotation plots follow a pairwise design in the current code.
The collinearity module prepares the pairwise relationships first, and Circos
uses one species pair to draw the final comparative plot.

For collinearity, ``workflow/rules/8_annotation_collinearity.smk`` builds all
pair combinations from the annotation species list when ``interspecific: true``
is enabled:

.. code-block:: text

   results/anno/collinearity/{species1}_vs_{species2}.collinearity.done

For Circos, ``workflow/rules/9_annotation_circos.smk`` always works on one
pair. If ``species_pair`` is set, the first two values are used. If it is empty,
the workflow uses the first two annotation-ready species from
``assembly-sheet.csv``.

.. code-block:: yaml

   params:
     annotation:
       circos:
         enable: true
         species_pair: ["Ath", "Mli"]

The Circos pair must have the paired inputs already available: final assemblies,
HiTE outputs, TE chromosome results, self-collinearity results for each species,
and the cross-species collinearity result for that pair.

Circos
------

Run Circos preparation and plotting for the first two available species, or for
the species pair configured in ``species_pair``:

.. code-block:: bash

   snakemake \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources \
     --until aggregate_circos_analysis

Main outputs:

.. code-block:: text

   results/anno/circos/te_family_selection.json
   results/anno/circos/circos_data/
   results/anno/circos/circos.conf
   results/anno/plot/{sp1}_vs_{sp2}_circos.png
   results/anno/plot/{sp1}_vs_{sp2}_circos.svg
   results/anno/plot/{sp1}_vs_{sp2}_circos_summary.txt

Circos parameters are set in ``/path/to/workdir/config/config.yaml``:

.. code-block:: yaml

   params:
     annotation:
       circos:
         enable: true
         species_pair: []
         te_family: "LTR_Copia"
         win_gc: 50000
         win_repeat: 50000
         win_gene: 100000
         ltr_win: 500000
         mu: 7e-9

The Circos plot includes GC density, overall repeat density, gene density, LTR
insertion age, self-collinearity links for each species, cross-species
collinearity links, and one selected TE family density track. By default,
``te_family: "LTR_Copia"`` requests the LTR_Copia track. If that family is not
available in both species, ``scripts/select_te_family.py`` falls back to the
TE family that is shared by the selected species and has the highest total
abundance across their TE chromosome density files. Set ``te_family: "auto"``
to always use this automatic selection. The ``win_*`` fields control the
window sizes for GC, repeat, gene, and LTR-age tracks, and ``mu`` should be set
to the mutation rate appropriate for the species pair.

Annotation Plot Outputs
-----------------------

The ``results/anno/plot/`` directory contains the following plot outputs from
the annotation module:

.. code-block:: text

   results/anno/plot/{species}/{species}_Distribution_of_TE_Classifications_pie.pdf
   results/anno/plot/{species}/{species}_Cumulative_Length_of_TE_Families.pdf
   results/anno/plot/{species}/{species}_Numerical_Abundance_of_Intact_TE_Families.pdf
   results/anno/plot/{species}/{species}_identity_values.pdf
   results/anno/plot/{species}/{species}_Kimura_divergence_landscape_of_TE.pdf
   results/anno/plot/{species}/{species}_Chromosomal_Distribution_of_Genes_and_TEs.pdf
   results/anno/plot/Cumulative_Length_of_TE_Families.pdf
   results/anno/plot/Genomic_Occupancy_of_TE_Families.pdf
   results/anno/plot/Numerical_Abundance_of_Intact_TE_Families.pdf
   results/anno/plot/identity_values.pdf
   results/anno/plot/Kimura_divergence_landscape_of_TE.pdf
   results/anno/plot/LTR_insertion_time.pdf
   results/anno/plot/{sp1}_vs_{sp2}_circos.png
   results/anno/plot/{sp1}_vs_{sp2}_circos.svg
   results/anno/plot/{sp1}_vs_{sp2}_circos_summary.txt

Single-Species Targets
----------------------

If you only want to test one species, target an output file directly. For
example:

.. code-block:: bash

   snakemake results/anno/standardized/Ath/Ath_standardized.out \
     -s /path/to/TE-flow/workflow/Snakefile \
     --use-conda \
     --directory /path/to/workdir \
     --cores 16 \
     --configfile /path/to/workdir/config/config.yaml \
     --config project_root=/path/to/TE-flow resource_root=/path/to/workdir/resources

Replace ``Ath`` with a ``sample_id`` from your project.
