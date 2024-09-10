import os
import shutil
from typing import Callable
import tum_esm_utils
from src import types, utils, retrieval

_RETRIEVAL_CODE_DIR = tum_esm_utils.files.rel_to_abs_path("../algorithms")
_CONTAINER_DIR = tum_esm_utils.files.rel_to_abs_path("../../../data/containers")


class ContainerFactory:
    """Factory for creating pylot containers.

    The pylot containers are created by copying the pylot code from the
    main directory and compiling the fortran code. Each container will
    have a unique id and is initialized with empty input and output
    directories.

    The factory keeps track of all containers and can remove them."""
    def __init__(
        self,
        config: types.Config,
        logger: retrieval.utils.logger.Logger,
        test_mode: bool = False,
    ):
        """Initialize the factory.

        The `__init__` function will download the Proffast 2.2 code
        from the KIT website."""

        self.config = config
        self.logger = logger
        self.containers: list[types.RetrievalContainer] = []

        assert self.config.retrieval is not None
        retrieval_algorithms = [
            job.retrieval_algorithm for job in self.config.retrieval.jobs
        ]

        if test_mode:
            self.logger.info(
                "Running in test mode (setting up all retrieval algorithms from scratch)"
            )
            for algorithm in [
                "proffast-1.0", "proffast-2.2", "proffast-2.3", "proffast-2.4"
            ]:
                shutil.rmtree(
                    os.path.join(_RETRIEVAL_CODE_DIR, algorithm, "main", "prf"),
                    ignore_errors=True
                )

        self.logger.info("Removing all old containers")
        self.remove_all_containers(include_unknown=True)
        self.logger.info("All old containers have been removed")

        for algorithm, initializer in [
            ("proffast-1.0", ContainerFactory.init_proffast10_code),
            ("proffast-2.2", ContainerFactory.init_proffast22_code),
            ("proffast-2.3", ContainerFactory.init_proffast23_code),
            ("proffast-2.4", ContainerFactory.init_proffast24_code),
            ("proffast-2.4.1", ContainerFactory.init_proffast24_code),
        ]:
            if (algorithm in retrieval_algorithms) or test_mode:
                self.logger.info(f"Initializing {algorithm} ContainerFactory")
                initializer(self.logger.info)
            else:
                self.logger.info(
                    f"Not initializing {algorithm} ContainerFactory (unused)"
                )

        self.logger.info("ContainerFactory is set up")

    def create_container(
        self,
        retrieval_algorithm: types.RetrievalAlgorithm,
    ) -> types.RetrievalContainer:
        """Create a new container and return it.

        The container is created by copying the pylot code from the main
        directory and compiling the fortran code. The container is then
        initialized with empty input and output directories."""

        new_container_id = utils.text.get_random_container_name(
            currently_used_names=[c.container_id for c in self.containers]
        )
        container: types.RetrievalContainer

        assert self.config.retrieval is not None
        match retrieval_algorithm:
            case "proffast-1.0":
                container = types.Proffast10Container(
                    container_id=new_container_id
                )
            case "proffast-2.2":
                container = types.Proffast22Container(
                    container_id=new_container_id
                )
            case "proffast-2.3":
                container = types.Proffast23Container(
                    container_id=new_container_id
                )
            case "proffast-2.4":
                container = types.Proffast24Container(
                    container_id=new_container_id
                )
            case "proffast-2.4.1":
                container = types.Proffast241Container(
                    container_id=new_container_id
                )

        # copy and install the retrieval code into the container
        retrieval_code_root_dir = os.path.join(
            _RETRIEVAL_CODE_DIR, retrieval_algorithm
        )
        shutil.copytree(
            os.path.join(retrieval_code_root_dir, "main"),
            container.container_path,
        )
        installer_script_path = os.path.join(
            retrieval_code_root_dir, "install.sh"
        )
        if os.path.isfile(installer_script_path):
            tum_esm_utils.shell.run_shell_command(
                command=installer_script_path,
                working_directory=container.container_path,
            )

        # generate empty input directory
        os.mkdir(container.data_input_path)
        os.mkdir(os.path.join(container.data_input_path, "ifg"))
        os.mkdir(os.path.join(container.data_input_path, "map"))
        os.mkdir(os.path.join(container.data_input_path, "log"))

        # generate empty output directory
        os.mkdir(container.data_output_path)

        # bundle container paths together
        self.containers.append(container)

        return container

    def remove_container(self, container_id: str) -> None:
        """Remove a container by its id.

        It will remove the pylot code, the input and output directories
        of the container. It raises an IndexError if no container with
        the given id exists.
        """
        try:
            container = [
                c for c in self.containers if c.container_id == container_id
            ][0]
            shutil.rmtree(container.container_path)
            shutil.rmtree(container.data_input_path)
            shutil.rmtree(container.data_output_path)
            self.containers.remove(container)
        except IndexError:
            raise ValueError(f'no container with id "{container_id}"')

    def remove_all_containers(self, include_unknown: bool = False) -> None:
        """Remove all containers."""
        if include_unknown:
            for d in os.listdir(_CONTAINER_DIR):
                subdir = os.path.join(_CONTAINER_DIR, d)
                if os.path.isdir(subdir):
                    shutil.rmtree(subdir)
        else:
            for container in self.containers:
                shutil.rmtree(container.container_path)
        self.containers = []

    @staticmethod
    def init_proffast10_code(_print: Callable[[str], None]) -> None:
        """Initialize the Proffast 1.0 code"""

        KIT_BASE_URL = "https://www.imk-asf.kit.edu/downloads/Coccon-SW/"
        ZIPFILE_NAME = "2021-03-08_prf96-EM27-fast.zip"
        ROOT_DIR = os.path.join(_RETRIEVAL_CODE_DIR, "proffast-1.0", "main")

        # DOWNLOAD PROFFAST 1.0 code if it doesn't exist yet
        if os.path.exists(os.path.join(ROOT_DIR, "prf")):
            _print(f"Proffast 1.0 has already been downloaded")
            return

        _print(f"Downloading Proffast 1.0 code")
        tum_esm_utils.shell.run_shell_command(
            command=f"wget --quiet {KIT_BASE_URL}/{ZIPFILE_NAME}",
            working_directory=ROOT_DIR,
        )
        tum_esm_utils.shell.run_shell_command(
            command=f"unzip -q {ZIPFILE_NAME}",
            working_directory=ROOT_DIR,
        )
        os.rename(
            os.path.join(ROOT_DIR, "2021-03-08_prf96-EM27-fast"),
            os.path.join(ROOT_DIR, "prf"),
        )

        # clean up unused directories
        for d in [
            os.path.join(ROOT_DIR, "prf", "preprocess", "125HR-garmisch"),
            os.path.join(ROOT_DIR, "prf", "preprocess", "125HR-karlsruhe"),
            os.path.join(ROOT_DIR, "prf", "preprocess", "sod2017_em27sn039"),
            os.path.join(ROOT_DIR, "prf", "out_fast", "sod2017_em27sn039"),
            os.path.join(
                ROOT_DIR, "prf", "out_fast", "sod2017_em27sn039_Linux"
            ),
            os.path.join(ROOT_DIR, "prf", "analysis"),
            os.path.join(ROOT_DIR, "prf", "source"),
        ]:
            shutil.rmtree(d)

        # clean up unused files
        for f in [
            os.path.join(ROOT_DIR, ZIPFILE_NAME),
            os.path.join(ROOT_DIR, "prf", "continue.txt"),
            os.path.join(
                ROOT_DIR, "prf", "inp_fast",
                "invers10_sod2017_em27sn039_170608.inp"
            ),
            os.path.join(
                ROOT_DIR, "prf", "inp_fast",
                "invers10_sod2017_em27sn039_170609.inp"
            ),
            os.path.join(
                ROOT_DIR, "prf", "inp_fast",
                "pcxs10_sod2017_em27sn039_170608.inp"
            ),
            os.path.join(
                ROOT_DIR, "prf", "inp_fast",
                "pcxs10_sod2017_em27sn039_170609.inp"
            ),
        ]:
            os.remove(f)

        # remove other unused files
        os.system("rm " + os.path.join(ROOT_DIR, "prf", "*.py"))
        os.system("rm " + os.path.join(ROOT_DIR, "prf", "invers10*"))
        os.system("rm " + os.path.join(ROOT_DIR, "prf", "pcxs10*"))

    @staticmethod
    def init_proffast22_code(_print: Callable[[str], None]) -> None:
        """Initialize the Proffast 2.2 and pylot 1.1 code.

        It will download the Proffast 2.2 code from the KIT website
        (https://www.imk-asf.kit.edu/downloads/Coccon-SW/PROFFASTv2.2.zip)
        and copy it to the directory `src/prfpylot/main/prf`."""

        KIT_BASE_URL = "https://www.imk-asf.kit.edu/downloads/Coccon-SW/"
        ZIPFILE_NAME = "PROFFASTv2.2.zip"
        ROOT_DIR = os.path.join(_RETRIEVAL_CODE_DIR, "proffast-2.2", "main")

        # DOWNLOAD PROFFAST 2.2 code if it doesn't exist yet
        if os.path.exists(os.path.join(ROOT_DIR, "prf")):
            _print(f"Proffast 2.2 has already been downloaded")
            return

        _print(f"Downloading Proffast 2.2 code")
        tum_esm_utils.shell.run_shell_command(
            command=f"wget --quiet {KIT_BASE_URL}/{ZIPFILE_NAME}",
            working_directory=ROOT_DIR,
        )
        tum_esm_utils.shell.run_shell_command(
            command=f"unzip -q {ZIPFILE_NAME}",
            working_directory=ROOT_DIR,
        )
        os.remove(os.path.join(ROOT_DIR, ZIPFILE_NAME))

    @staticmethod
    def init_proffast23_code(_print: Callable[[str], None]) -> None:
        """Initialize the Proffast 2.3 and pylot 1.2 code.

        It will download the Proffast 2.3 code from the KIT website
        (https://www.imk-asf.kit.edu/downloads/Coccon-SW/PROFFASTv2.3.zip)
        and copy it to the directory `src/prfpylot/main/prf`."""

        KIT_BASE_URL = "https://www.imk-asf.kit.edu/downloads/Coccon-SW/"
        ZIPFILE_NAME = "PROFFASTv2.3.zip"
        ROOT_DIR = os.path.join(_RETRIEVAL_CODE_DIR, "proffast-2.3", "main")

        # DOWNLOAD PROFFAST 2.3 code if it doesn't exist yet
        if os.path.exists(os.path.join(ROOT_DIR, "prf")):
            _print(f"Proffast 2.3 has already been downloaded")
            return

        _print(f"Downloading Proffast 2.3 code")
        tum_esm_utils.shell.run_shell_command(
            command=f"wget --quiet {KIT_BASE_URL}/{ZIPFILE_NAME}",
            working_directory=ROOT_DIR,
        )
        tum_esm_utils.shell.run_shell_command(
            command=f"unzip -q {ZIPFILE_NAME}",
            working_directory=ROOT_DIR,
        )
        os.remove(os.path.join(ROOT_DIR, ZIPFILE_NAME))

    @staticmethod
    def init_proffast24_code(_print: Callable[[str], None]) -> None:
        """Initialize the Proffast 2.4 and pylot 1.3 code.

        It will download the Proffast 2.4 code from the KIT website
        (https://www.imk-asf.kit.edu/downloads/Coccon-SW/PROFFASTv2.4.zip)
        and copy it to the directory `src/prfpylot/main/prf`."""

        KIT_BASE_URL = "https://www.imk-asf.kit.edu/downloads/Coccon-SW/"
        ZIPFILE_NAME = "PROFFASTv2.4.zip"
        ROOT_DIR = os.path.join(_RETRIEVAL_CODE_DIR, "proffast-2.4", "main")

        # DOWNLOAD PROFFAST 2.4 code if it doesn't exist yet
        if os.path.exists(os.path.join(ROOT_DIR, "prf")):
            _print(f"Proffast 2.4 has already been downloaded")
            return

        _print(f"Downloading Proffast 2.4 code")
        tum_esm_utils.shell.run_shell_command(
            command=f"wget --quiet {KIT_BASE_URL}/{ZIPFILE_NAME}",
            working_directory=ROOT_DIR,
        )
        tum_esm_utils.shell.run_shell_command(
            command=f"unzip -q {ZIPFILE_NAME}",
            working_directory=ROOT_DIR,
        )
        os.remove(os.path.join(ROOT_DIR, ZIPFILE_NAME))

        # copy adapted Preprocess 6 source code
        ORIGINAL_SOURCE_FILE = os.path.join(
            _RETRIEVAL_CODE_DIR, "proffast-2.4", "main", "prf", "source",
            "preprocess", "preprocess6.F90"
        )
        ADAPTED_SOURCE_FILE = os.path.join(
            _RETRIEVAL_CODE_DIR, "proffast-2.4", "source", "preprocess",
            "preprocess6.F90"
        )
        os.remove(ORIGINAL_SOURCE_FILE)
        shutil.copyfile(ADAPTED_SOURCE_FILE, ORIGINAL_SOURCE_FILE)

    @staticmethod
    def init_proffast241_code(_print: Callable[[str], None]) -> None:
        ROOT_DIR = os.path.join(_RETRIEVAL_CODE_DIR, "proffast-2.4.1", "main")

        if os.path.exists(os.path.join(ROOT_DIR, "prf")):
            _print(f"Proffast 2.41 has already been downloaded")
            return

        raise NotImplementedError(
            "Proffast 2.4.1 is not yet available to the public"
        )
