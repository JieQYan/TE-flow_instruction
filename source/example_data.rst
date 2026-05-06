Example Data
============

This page records the public data sources used as example inputs for TE-flow
documentation and testing. The raw datasets themselves are not redistributed
with TE-flow. Instead, TE-flow provides a helper script,
``test_data/download_databases.sh``, that downloads the source data from the
original repositories and prepares example sample sheets. Users should still
cite the corresponding source publications and database accessions when using
these data.

Species Used in the Examples
----------------------------

The example project uses two species identifiers:

.. code-block:: text

   Ath  Arabidopsis thaliana
   Mli  Meniocus linifolius

These identifiers are used consistently in sample sheets and output paths, for
example ``resources/assembly-sheet.csv``, ``resources/rnaseq-sheet.csv``,
``resources/epigenetic-sheet.csv``, and ``resources/refs/``.

Assembly and Reference Genome Data
----------------------------------

Arabidopsis thaliana (Ath)
~~~~~~~~~~~~~~~~~~~~~~~~~~

Raw assembly sequencing data for ``Ath`` include PacBio HiFi reads, Oxford
Nanopore long reads, Illumina short reads, and Hi-C Illumina reads. These data
were deposited in the
`Genome Sequence Archive (GSA) <https://ngdc.cncb.ac.cn/gsa/>`__ at the
National Genomics Data Center, Beijing Institute of Genomics, Chinese Academy
of Sciences / China National Center for Bioinformation under accession
`CRA004538 <https://ngdc.cncb.ac.cn/gsa/browse/CRA004538>`__.

The assembled reference genome used for ``Ath`` is available from
`Genome Warehouse (GWH) <https://ngdc.cncb.ac.cn/gwh/>`__ under accession
`GWHBDNP00000000.1 <https://ngdc.cncb.ac.cn/gwh/Assembly/21820/show>`__.

The corresponding genome annotation is available from Figshare through DOI
`10.6084/m9.figshare.14913045 <https://doi.org/10.6084/m9.figshare.14913045>`__.

The primary data-availability statement for these resources is given in:
`High-quality Arabidopsis thaliana Genome Assembly with Nanopore and HiFi Long
Reads <https://academic.oup.com/gpb/article/20/1/4/7230403>`__.

Meniocus linifolius (Mli)
~~~~~~~~~~~~~~~~~~~~~~~~~

For ``Mli``, the example assembly inputs include HiFi and Hi-C sequencing data.
The assembled genome and annotation files are from the same public project.
Genome assemblies, annotations, and sequence data were deposited in the
`CNSA database <https://db.cngb.org/cnsa/>`__ under project number
`CNP0003993 <https://db.cngb.org/search/?q=CNP0003993>`__.

The data-availability statement for this project is associated with:
`Genomes of Meniocus linifolius and Tetracme quadricornis reveal the ancestral
karyotype and genomic features of core Brassicaceae
<https://www.sciencedirect.com/science/article/pii/S2590346224001202>`__.

Expression Data
---------------

The ``Ath`` RNA-seq example uses Arabidopsis accession 6909 and includes
seedlings, 9-leaf rosettes, flowers, and pollen tissues. The data are available
from NCBI GEO under accession
`GSE226691 <https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE226691>`__.

These RNA-seq data correspond to the tissue set described in the data
availability statement of:
`Population-level annotation of lncRNAs in Arabidopsis thaliana reveals
extensive expression and epigenetic variability associated with TE-like
silencing <https://academic.oup.com/plcell/article/36/1/85/7264822>`__.

Epigenetic Data
---------------

BS-seq
~~~~~~

The ``Ath`` BS-seq example uses Arabidopsis accession 6909. Four replicate
BS-seq datasets are used as methylation inputs. The data are available from
NCBI GEO under accession
`GSE226560 <https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE226560>`__.

ChIP-seq
~~~~~~~~

The ``Ath`` ChIP-seq example uses Arabidopsis accession 6909 H3K27me3 ChIP-seq
data together with the corresponding input control. The data are available from
NCBI GEO under accession
`GSE226682 <https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE226682>`__.

The BS-seq and ChIP-seq accessions are also described in the data availability
statement of the same Arabidopsis lncRNA study linked above.

Example File Placement
----------------------

The helper script writes downloaded files under ``test_data/``:

.. code-block:: text

   test_data/raw/assembly/
   test_data/raw/rnaseq/
   test_data/raw/epigenetic/
   test_data/resources/refs/
   test_data/sample_sheets/

To run TE-flow with the default configuration, copy or link the generated sample
sheets and reference files into the runtime layout described in
:ref:`expected-runtime-inputs`. Reference FASTA and GFF3 files should be
available under ``resources/refs/`` using species-based names such as:

.. code-block:: text

   resources/refs/Ath.fa
   resources/refs/Ath.gene.gff3
   resources/refs/Mli.fa
   resources/refs/Mli.gene.gff3

The script also creates example sample sheets in ``test_data/sample_sheets/``.
They use the same species identifiers, ``Ath`` and ``Mli``, so that assembly,
annotation, expression, and epigenetic outputs can be connected across modules.
