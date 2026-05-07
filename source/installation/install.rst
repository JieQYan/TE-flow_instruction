Install
=======

Repository Setup
----------------

Clone the repository and move into the project root:

.. code-block:: bash

   git clone https://github.com/JieQYan/TE-flow.git TE-flow
   cd TE-flow

The repository layout used by the workflow is:

.. code-block:: text

   TE-flow/
   |-- bin/
   |-- config/
   |-- docker/
   |-- docs/
   |-- scripts/
   |-- test_data/
   |-- workflow/
   `-- resources/

``test_data/`` contains helper files for downloading public example data, such
as ``test_data/download_databases.sh``. The workflow itself reads runtime
inputs from the paths configured in ``config/config.yaml`` and the sample sheets
under ``resources/`` unless you point those settings to another location.

Docker Image for HiTE, RepeatMasker, and Juicer
-----------------------------------------------

TE-flow includes a Docker build context at:

.. code-block:: text

   docker/hite-repeatmasker-juicer/

Build the image from the repository root:

.. code-block:: bash

   docker build \
     -f docker/hite-repeatmasker-juicer/Dockerfile \
     -t teflow/te-flow:1.0 \
     .

Current repository defaults commonly refer to the image name
``teflow/te-flow:1.0`` in runtime examples below. Use one of
the following approaches:

* build the image with the tag expected by your config
* or update ``config.yaml`` so ``params.annotation.hite.image``,
  ``params.annotation.repeatmasker.docker_image``, and
  ``params.scaffolding.juicer_tools_docker_image`` point to the tag you built

The Dockerfile currently installs these components in fixed container paths:

* RMBlast: ``/opt/rmblast/bin``
* TRF: ``/opt/trf/bin/trf``
* RepeatMasker: ``/opt/RepeatMasker``
* Juicer: ``/opt/juicer-1.6``
* Juicer tools jar:
  ``/opt/juicer-1.6/CPU/common/juicer_tools.1.9.9_jcuda.0.8.jar``

RepeatMasker Database and Initialization
----------------------------------------

The workflow image installs RepeatMasker, but it does not bundle the Dfam
database or finish RepeatMasker's interactive configuration step. If you want
standardized TE names and family assignments to follow existing
RepeatMasker / Dfam conventions, prepare the database first and then run the
initialization helper.

1. Download or prepare a RepeatMasker database.

   RepeatMasker can use custom TE libraries or Dfam-compatible database files.
   Dfam ``FamDB`` HDF5 libraries are split into numbered taxonomic
   partitions. At a minimum, download the root partition, numbered ``0``,
   because it contains information required by RepeatMasker/FamDB. Additional
   partitions can be added according to the taxa you plan to annotate.

   FamDB files can be downloaded from:

   `https://www.dfam.org/releases/current/families/FamDB <https://www.dfam.org/releases/current/families/FamDB>`_

   Optionally, the last Repbase RepeatMasker Edition library can also be
   combined with Dfam if you have access to that database.

2. Make the database available inside the container.

   With the default TE-flow config, RepeatMasker expects the database at:

   .. code-block:: text

      /opt/RepeatMasker/Libraries/famdb

   The corresponding config entries are:

   * ``annotation.repeatmasker.famdb_script``
   * ``annotation.repeatmasker.famdb_dir``

   You can either put the ``FamDB`` files directly in that container path or
   keep them on the host and mount them into the container.

   To place the files inside a container environment, start an interactive
   container from the host system:

   .. code-block:: bash

      docker run --rm -it teflow/te-flow:1.0 bash

   Then copy or download the ``FamDB`` files into:

   .. code-block:: text

      /opt/RepeatMasker/Libraries/famdb

   To keep the files on the host, mount your host-side FamDB directory into the
   expected container path:

   .. code-block:: bash

      docker run --rm -it \
        -v /path/to/FamDB:/opt/RepeatMasker/Libraries/famdb \
        teflow/te-flow:1.0 bash

3. Run the RepeatMasker initialization helper.

   After the database files are available at the expected path, run the helper
   from the host system:

   .. code-block:: bash

      docker run --rm -it teflow/te-flow:1.0 init_repeatmasker.sh

   This starts a new container from ``teflow/te-flow:1.0`` and runs
   ``init_repeatmasker.sh`` automatically inside that container.

The helper script ``docker/hite-repeatmasker-juicer/init_repeatmasker.sh``
configures RepeatMasker with:

* TRF: ``/opt/trf/bin/trf``
* RMBlast: ``/opt/rmblast/bin``

If the Dfam database is unavailable, the workflow can still run HiTE-based TE
annotation, but RepeatMasker normalization may be skipped or fall back to
filtered HiTE outputs during standardization. In that case, TE naming and
family labels will be less directly aligned with existing RepeatMasker / Dfam
conventions.

.. _working-directory-and-resource-directory:

Working Directory and Resource Directory
----------------------------------------

TE-flow separates the code repository from runtime inputs and outputs. A common
layout is:

.. code-block:: text

   /path/to/
   |-- TE-flow/
   `-- workdir/
       |-- config/
       |   `-- config.yaml
       |-- resources/
       |   |-- assembly-sheet.csv
       |   |-- rnaseq-sheet.csv
       |   |-- epigenetic-sheet.csv
       |   |-- refs/
       |   `-- secret.pass
       |-- results/
       `-- logs/

Runtime inputs commonly referenced by the workflow include:

* ``resources/assembly-sheet.csv``
* ``resources/rnaseq-sheet.csv``
* ``resources/epigenetic-sheet.csv``
* files under ``resources/refs/``
* ``resources/secret.pass`` for Docker steps that use ``sudo``

The wrapper ``bin/TE-flow.py`` and the main ``workflow/Snakefile`` both support
resolving these runtime files through an explicit resource directory.
Detailed file naming conventions for sample sheets, ``resources/refs/``
contents, chromosome naming, and ``secret.pass`` are described in
:ref:`Expected Runtime Inputs <expected-runtime-inputs>`.

.. _configuration-template:

Configuration Template
----------------------

Start from the repository template:

.. code-block:: bash

   mkdir -p /path/to/workdir/config
   cp config/config.yaml /path/to/workdir/config/config.yaml

Then edit the copied file for your project. The fields most commonly changed
for a new run are:

* ``run_assembly``, ``run_annotation``, ``run_expression``,
  ``run_epigenetic``
* ``assembly_sheet``, ``rnaseq_sheet``, ``epigenetic_sheet``
* ``species_map``, ``lineage``, and annotation ``mutation_rate``. For BUSCO
  ``lineage`` values, see the
  `BUSCO lineage datasets <https://busco-data.ezlab.org/v5/data/lineages/>`_.
* ``image``, ``docker_image``, and ``juicer_tools_docker_image`` only if you
  built or pulled a different image tag

Most resource-related paths can stay at their default ``resources/...`` values
when you follow the directory layout described above. A minimal edited
``config.yaml`` usually looks like:

.. code-block:: yaml

   run_assembly: true
   run_annotation: true
   run_expression: true
   run_epigenetic: true

   assembly_sheet: "resources/assembly-sheet.csv"

   params:
     annotation:
       tesorter:
         mutation_rate: 7e-9
       repeatmasker:
         species_map:
           Ath: "Arabidopsis thaliana"
           Mli: "Meniocus linifolius"
     evaluation:
       busco:
         lineage: "brassicales_odb12"
     epigenetic:
       epigenetic_sheet: "resources/epigenetic-sheet.csv"
     expression:
       rnaseq_sheet: "resources/rnaseq-sheet.csv"

Update ``species_map`` so each sample ID in your project maps to the Dfam
species name that RepeatMasker should use. For example, replace ``Ath`` and
``Mli`` with your own sample IDs and species names. Update ``mutation_rate``
according to the annotated species before using LTR insertion-time plots. Keep
sample sheets, ``sudo_password_file``, and ``gene_gff_dir`` as
``resources/...`` paths unless you intentionally store them elsewhere.

When ``--resources`` is provided, TE-flow uses that directory first for
``resources/...`` paths. For example, with this config:

.. code-block:: yaml

   params:
     expression:
       rnaseq_sheet: "resources/rnaseq-sheet.csv"

and this command:

.. code-block:: bash

   python3 bin/TE-flow.py expression \
     --workdir /path/to/workdir \
     --resources /data/my_resources

TE-flow reads ``/data/my_resources/rnaseq-sheet.csv``. If that file is not
there, it falls back to ``/path/to/workdir/resources/rnaseq-sheet.csv`` and
then to the repository copy. Absolute paths are used exactly as written.
Container paths such as ``/opt/RepeatMasker/Libraries/famdb`` are different:
they belong to the Docker image, so leave them unchanged unless you build a
custom image.

Typical Execution
-----------------

Run modules through the wrapper:

.. code-block:: bash

   python3 bin/TE-flow.py assembly \
     --workdir /path/to/workdir \
     --cores 16

   python3 bin/TE-flow.py anno \
     --workdir /path/to/workdir \
     --resources /path/to/workdir/resources \
     --cores 16

   python3 bin/TE-flow.py expression \
     --workdir /path/to/workdir \
     --resources /path/to/workdir/resources \
     --cores 16

   python3 bin/TE-flow.py epigenetic \
     --workdir /path/to/workdir \
     --resources /path/to/workdir/resources \
     --cores 16

The wrapper invokes Snakemake with ``--use-conda`` internally, so conda
environments defined in ``workflow/envs/`` can be created automatically during
execution.

Or run Snakemake directly:

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

Notes
-----

* The annotation module depends on the Docker image being available and
  correctly configured.
* The expression and epigenetic modules depend on the corresponding sample
  sheets being present under the runtime resource directory.
* Assembly, annotation, expression, and epigenetic outputs are connected by the
  Snakemake DAG, so upstream files may be rebuilt when provenance or parameters
  change.
