import sys
from pathlib import Path
from typing import List, Optional, Union

from pydantic import DirectoryPath, Field

from ._basemodel import BaseModel
from ._description_helpers import formatter as f
from ._dimensions import CoupledDim, OperationDim
from ._imas import ImasBaseModel
from .data_location import DataLocation
from .matrix_samplers import (CartesianProduct, HaltonSampler, LHSSampler,
                              SobolSampler)
from .variables import VariableConfigModel
from .workdir import WorkDirectoryModel

if sys.version_info <= (3, 7):
    from typing_extensions import Literal
else:
    from typing import Literal


class CreateConfigModel(BaseModel):
    """The options of the `create` subcommand are stored in the `create` key in
    the config."""
    dimensions: List[Union[CoupledDim, OperationDim]] = Field(description=f("""
        The `dimensions` specifies the dimensions of the matrix to sample
        from. Each dimension is a compound set of operations to apply.
        From this, a matrix all possible combinations is generated.
        Essentially, it generates the
        [Cartesian product](en.wikipedia.org/wiki/Cartesian_product)
        of all operations. By specifying a different `sampler`, a subset of
        this hypercube can be efficiently sampled.
        """))

    sampler: Union[LHSSampler, HaltonSampler, SobolSampler,
                   CartesianProduct] = Field(default=CartesianProduct(),
                                             discriminator='method',
                                             description=f("""
        For efficient UQ, it may not be necessary to sample the entire matrix
        or hypercube. By default, the cartesian product is taken
        (`method: cartesian-product`). For more efficient sampling of the space,
        the following `method` choices are available:
        [`latin-hypercube`](en.wikipedia.org/wiki/Latin_hypercube_sampling),
        [`sobol`](en.wikipedia.org/wiki/Sobol_sequence),
        [`halton`](en.wikipedia.org/wiki/Halton_sequence).
        Where `n_samples` gives the number of samples to extract.
        """))

    template: DirectoryPath = Field(description=f("""
        Template directory to modify. Duqtools copies and updates the settings
        required for the specified system from this directory. This can be a
        directory with a finished run, or one just stored by JAMS (but not yet
        started). By default, duqtools extracts the input IMAS database entry
        from the settings file (e.g. jetto.in) to find the data to modify for
        the UQ runs.
        """))

    template_data: Optional[ImasBaseModel] = Field(description=f("""
        Specify the location of the template data to modify. This overrides the
        location of the data specified in settings file in the template
        directory.
        """))

    data: DataLocation = Field(description=f("""
        Where to store the in/output IDS data.
        The data key specifies the machine or imas
        database name where to store the data (`imasdb`). duqtools will write the input
        data files for UQ start with the run number given by `run_in_start_at`.
        The data generated by the UQ runs (e.g. from jetto) will be stored
        starting by the run number given by `run_out_start_at`.
        """))


class SubmitConfigModel(BaseModel):
    """The options of the `submit` subcommand are stored under the `submit` key
    in the config.

    The config describes the commands to start the UQ runs.
    """

    submit_script_name: str = Field(
        '.llcmd', description='Name of the submission script.')
    submit_command: str = Field('sbatch',
                                description='Submission command for slurm.')
    submit_system: Literal['prominence', 'slurm'] = Field(
        'slurm',
        description='System to submit jobs to [slurm (default), prominence]')


class StatusConfigModel(BaseModel):
    """The options of the `status` subcommand are stored under the `status` key
    in the config.

    These only need to be changed if the modeling software changes.
    """

    status_file: str = Field('jetto.status',
                             description='Name of the status file.')
    in_file: str = Field('jetto.in',
                         description=f("""
            Name of the modelling input file, will be used to check
            if the subprocess has started.
            """))

    out_file: str = Field('jetto.out',
                          description=f("""
            Name of the modelling output file, will be used to
            check if the software is running.
            """))

    msg_completed: str = Field('Status : Completed successfully',
                               description=f("""
            Parse `status_file` for this message to check for
            completion.
            """))

    msg_failed: str = Field('Status : Failed',
                            description=f("""
            Parse `status_file` for this message to check for
            failures.
            """))

    msg_running: str = Field('Status : Running',
                             description=f("""
            Parse `status_file` for this message to check for
            running status.
            """))


class MergeStep(BaseModel):
    """These parameters describe which paths should be merged.

    Three sets of variables need to be defined:
    - time_variable: this points to the data for the time coordinate
    - grid_variable: this points to the data for the grid variable
    - data_variables: these point to the data to be merged

    Note that all variables must be from the same IDS.

    The grid and data variables must share a common dimension. The grid variable
    will be used to rebase all data variables to a common grid.

    The time variable will be used to rebase the grid variable and the data variables
    to a common time coordinate. To denote the time index, use `/*/` in both
    the grid and data variables.

    Rebasing involves interpolation.

    Note that multiple merge steps can be specified, for example for different
    IDS.
    """
    data_variables: List[str] = Field(description=f("""
            This is a list of data variables to be merged. This means
            that the mean and error for these data over all runs are calculated
            and written back to the ouput data location.
            The paths should contain `/*/` for the time component or other dimensions.
            """))
    grid_variable: str = Field(description=f("""
            This variable points to the data for the grid coordinate. It must share a common
            placeholder dimension with the data variables.
            It will be used to rebase all data variables to same (radial) grid before merging
            using interpolation.
            The path should contain '/*/' to denote the time component or other dimension.
            """))
    time_variable: str = Field(description=f("""
            This variable determines the time coordinate to merge on. This ensures
            that the data from all runs are on the same time coordinates before
            merging.
            """))


class MergeConfigModel(BaseModel):
    """The options of the `merge` subcommand are stored under the `merge` key
    in the config.

    These keys define the location of the IMAS data, which IDS entries
    to merge, and where to store the output.

    Before merging, all keys are rebased on (1) the same radial
    coordinate specified via `base_ids` and (2) the timestamp.
    """
    data: Path = Field('runs.yaml',
                       description=f("""
            Data file with IMAS handles, such as `data.csv` or `runs.yaml`'
            """))
    template: ImasBaseModel = Field(description=f("""
            This IMAS DB entry will be used as the template.
            It is copied to the output location.
            """))
    output: ImasBaseModel = Field(
        description='Merged data will be written to this IMAS DB entry.')
    plan: List[MergeStep] = Field(description='List of merging operations.')


class ConfigModel(BaseModel):
    """The options for the CLI are defined by this model."""
    submit: SubmitConfigModel = Field(
        SubmitConfigModel(),
        description='Configuration for the submit subcommand')

    create: Optional[CreateConfigModel] = Field(
        description='Configuration for the create subcommand')

    status: StatusConfigModel = Field(
        StatusConfigModel(),
        description='Configuration for the status subcommand')

    merge: Optional[MergeConfigModel] = Field(
        description='Configuration for the merge subcommand')

    workspace: WorkDirectoryModel

    extra_variables: Optional[VariableConfigModel] = Field(
        description='Specify extra variables for this run.')

    system: Literal['jetto', 'dummy', 'jetto-pythontools',
                    'jetto-duqtools'] = Field(
                        'jetto', description='backend system to use')

    quiet: bool = Field(
        False,
        description='dont output to stdout, except for mandatory prompts')
