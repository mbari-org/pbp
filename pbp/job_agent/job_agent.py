from pathlib import Path
from datetime import timedelta, datetime
import os
import time
from loguru import logger  # A great logger option.
import sys


class JobAgent:
    """This class structure is designed to encapsulate the entire pbp process suite in a simple agent that performs all tasks, more automation with fewer parameters and no URI interface."""

    def __init__(
        self,
        output_prefix,  # Name of the deployment
        recorder,  # Recorder type
        audio_base_dir,  # Audio base directory
        json_base_dir,  # JSON base directory
        start,  # Start date
        end,  # End date
        prefix,  # Prefix
        nc_output_dir,  # NetCDF output directory
        global_attrs,  # Global attributes file
        variable_attrs,  # Variable attributes file
        latlon,  # Latitude and Longitude
        title,  # Title
        cmlim,  # CMLIM
        ylim,  # YLIM
        log_dir,  # Log directory
        meta_output_dir=None,
        xml_dir=None,
        sensitivity_flat_value=None,
        sensitivity_uri=None,
        voltage_multiplier=None,
        subset_to=None,
    ):
        self.output_prefix = output_prefix
        if not self.output_prefix.endswith("_"):
            self.output_prefix += "_"

        self.output_prefix = self.output_prefix.replace("__", "_")

        if (
            meta_output_dir is None
        ):  # Sets the log directory the same as the json base directory if not specified which feels like a good best practice.
            meta_output_dir = json_base_dir
        if meta_output_dir == "":
            meta_output_dir = json_base_dir
        self.name = self.output_prefix
        if self.name.endswith("_"):
            self.name = self.name[:-1]

        self.recorder = recorder
        self.audio_base_dir = audio_base_dir

        if os.name == "nt":  # If machine running the job agent is Windows.
            self.uri = Path(os.path.normpath(self.audio_base_dir))
            self.meta_output_dir = Path(os.path.normpath(meta_output_dir))
            self.json_base_dir = Path(os.path.normpath(json_base_dir))
            if xml_dir is not None and xml_dir != "":
                self.xml_dir = Path(os.path.normpath(xml_dir))

            self.nc_output_dir = Path(os.path.normpath(nc_output_dir))
            self.global_attrs = Path(os.path.normpath(global_attrs))
            self.variable_attrs = Path(os.path.normpath(variable_attrs))
            self.log_dir = Path(os.path.normpath(log_dir))

            if self.recorder == "NRS":
                self.voltage_multiplier = str(voltage_multiplier)
                self.sensitivity_uri = Path(os.path.normpath(sensitivity_uri))
            if self.recorder == "SOUNDTRAP":
                self.sensitivity_flat_value = str(sensitivity_flat_value)

        if os.name == "posix":  # If machine running the job agent is Unix-based.
            self.uri = Path(self.audio_base_dir).resolve().as_uri()
            self.meta_output_dir = Path(os.path.normpath(meta_output_dir)).as_posix()
            self.json_base_dir = Path(os.path.normpath(json_base_dir)).as_posix()
            self.xml_dir = Path(os.path.normpath(xml_dir)).as_posix()
            self.nc_output_dir = Path(os.path.normpath(nc_output_dir)).as_posix()
            self.global_attrs = Path(os.path.normpath(global_attrs)).as_posix()
            self.variable_attrs = Path(os.path.normpath(variable_attrs)).as_posix()
            self.log_dir = Path(os.path.normpath(log_dir)).as_posix()

            if self.recorder == "NRS":
                self.voltage_multiplier = str(voltage_multiplier)
                self.sensitivity_uri = Path(os.path.normpath(sensitivity_uri))
            if self.recorder == "SOUNDTRAP":
                self.sensitivity_flat_value = str(sensitivity_flat_value)

        self.prefix = str(prefix)  # Prefix
        self.start_date = datetime.strptime(str(start), "%Y%m%d").date()
        self.end_date = datetime.strptime(str(end), "%Y%m%d").date()

        self.latlon = latlon
        self.title = title
        self.cmlim = cmlim
        self.ylim = ylim

        if subset_to in [None, ""]:
            subset_to = ylim

        self.subset_to = subset_to

        log_filename_str = (
            "pbp-job-agent_"
            + self.output_prefix
            + "_"
            + str(start)
            + "_"
            + str(end)
            + ".log"
        )
        log_filename_str = log_filename_str.replace("___", "__")
        log_filename_str = log_filename_str.replace("__", "_")

        self.log_dir = log_dir
        self.log_filename_str = log_filename_str

        logger.add(
            os.path.join(self.log_dir, self.log_filename_str),
            format="{extra[name]} | {time:YYYYMMDD:HH:mm:ss:SSS} | {level} | {message}",
            level="DEBUG",
        )

    def info_log(self, message):
        logger.bind(name=self.name).opt(colors=True).info("<blue>" + message + "</blue>")

    def error_log(self, message):
        logger.bind(name=self.name).opt(colors=True).error("<red>" + message + "</red>")

    def warning_log(self, message):
        logger.bind(name=self.name).opt(colors=True).warning(
            "<yellow>" + message + "</yellow>"
        )

    def debug_log(self, message):
        logger.bind(name=self.name).opt(colors=True).debug(
            "<green>" + message + "</green>"
        )

    def search_filenames(self, directory, pattern):
        try:
            # List all files in the directory
            files = os.listdir(directory)

            # Check if any file contains the pattern
            for file in files:
                if pattern in file:
                    return True
            return False  # Return False if no file contains the pattern
        except FileNotFoundError:
            return False  # Return False if the directory doesn't exist

    def synth_pbp_meta_gen(
        self, recorder, uri, output_dir, json_base_dir, start, end, prefix, xml_dir=None
    ):
        command = "pbp-meta-gen"

        # Check if recorder is not None or an empty string
        if recorder not in [None, ""]:
            command += f" --recorder {recorder}"

        # Check if uri is not None or an empty string
        if uri not in [None, ""]:
            command += f" --uri {uri}"

        # Check if output_dir is not None or an empty string
        if output_dir not in [None, ""]:
            command += f" --output-dir {output_dir}"

        # Check if json_base_dir is not None or an empty string
        if json_base_dir not in [None, ""]:
            command += f" --json-base-dir {json_base_dir}"

        # Check if xml_dir is not None or an empty string
        if xml_dir not in [None, ""]:
            command += f" --xml-dir {xml_dir}"

        # Check if start is not None or an empty string
        if start not in [None, ""]:
            command += f" --start {start}"

        # Check if end is not None or an empty string
        if end not in [None, ""]:
            command += f" --end {end}"

        # Check if prefix is not None or an empty string
        if prefix not in [None, ""]:
            command += f" --prefix {prefix}"

        return command

    def synth_pbp_hmb_gen(
        self,
        date,
        json_base_dir,
        audio_base_dir,
        output_dir,
        global_attrs,
        variable_attrs,
        output_prefix,
        sensitivity_flat_value=None,
        sensitivity_uri=None,
        voltage_multiplier=None,
        subset_to=None,
    ):
        command = "pbp-hmb-gen"

        # Add --date flag only if date is not None or empty
        if date not in [None, ""]:
            command += f" --date {date}"

        # Add --json-base-dir flag only if json_base_dir is not None or empty
        if json_base_dir not in [None, ""]:
            command += f" --json-base-dir {str(json_base_dir)}"

        # Add --audio-base-dir flag only if audio_base_dir is not None or empty
        if audio_base_dir not in [None, ""]:
            command += f" --audio-base-dir {str(audio_base_dir)}"

        # Add --output-dir flag only if output_dir is not None or empty
        if output_dir not in [None, ""]:
            command += f" --output-dir {str(output_dir)}"

        # Add --global-attrs flag only if global_attrs is not None or empty
        if global_attrs not in [None, ""]:
            command += f" --global-attrs {str(global_attrs)}"

        # Add --variable-attrs flag only if variable_attrs is not None or empty
        if variable_attrs not in [None, ""]:
            command += f" --variable-attrs {str(variable_attrs)}"

        # Add --output-prefix flag only if output_prefix is not None or empty
        if output_prefix not in [None, ""]:
            command += f" --output-prefix {output_prefix}"

        # Add --sensitivity-flat-value flag only if sensitivity_flat_value is not None or empty
        if sensitivity_flat_value not in [None, ""]:
            command += f" --sensitivity-flat-value {sensitivity_flat_value}"

        # Add --sensitivity-uri flag only if sensitivity_flat_value is not None or empty
        if sensitivity_uri not in [None, ""]:
            command += f" --sensitivity-uri {sensitivity_uri}"

        # Add --sensitivity-uri flag only if sensitivity_flat_value is not None or empty
        if voltage_multiplier not in [None, ""]:
            command += f" --voltage-multiplier {voltage_multiplier}"

        if subset_to not in [None, ""]:
            command += f" --subset-to {subset_to}"

        return command

    def synth_pbp_plot_gen(self, latlon, title, cmlim, ylim, nc_file):
        command = "pbp-hmb-plot"

        # Add --latlon flag if latlon is not None or empty string
        if latlon not in [None, ""]:
            command += f" --latlon {latlon}"

        # Add --title flag if title is not None or empty string
        if title not in [None, ""]:
            command += f" --title {title}"

        # Add --cmlim flag if cmlim is not None or empty string
        if cmlim not in [None, ""]:
            command += f" --cmlim {cmlim}"

        # Add --ylim flag if ylim is not None or empty string
        if ylim not in [None, ""]:
            command += f" --ylim {ylim}"

        # Add nc_file if nc_file is not None or empty string
        if nc_file not in [None, ""]:
            command += f" {str(nc_file)}"

        return command

    def run(self):
        logger.add(
            os.path.join(self.log_dir, self.log_filename_str),
            format="{extra[name]} | {time:YYYYMMDD:HH:mm:ss:SSS} | {level} | {message}",
            level="DEBUG",
        )

        logger.bind(name=self.name).opt(colors=True).info(
            "<blue>Initializing the pbp/pypam processing suite.</blue>"
        )

        """Metadata generation and logs"""

        if self.recorder == "SOUNDTRAP":
            command = self.synth_pbp_meta_gen(
                self.recorder,
                self.uri,
                self.meta_output_dir,
                self.json_base_dir,
                self.start_date.strftime("%Y%m%d"),
                self.end_date.strftime("%Y%m%d"),
                self.prefix,
                self.xml_dir,
            )

        if self.recorder == "NRS":
            command = self.synth_pbp_meta_gen(
                self.recorder,
                self.uri,
                self.meta_output_dir,
                self.json_base_dir,
                self.start_date.strftime("%Y%m%d"),
                self.end_date.strftime("%Y%m%d"),
                self.prefix,
            )

        logger.bind(name=self.name).opt(colors=True).info(
            "<blue>Initiating processing for audio file and netCDF generation associated with : "
            + str(self.start_date)
            + "</blue>"
        )
        logger.bind(name=self.name).opt(colors=True).info(
            "<green>running > " + command + "</green>"
        )

        # Excecutes the meta-gen command
        os.system(command)

        delta = timedelta(days=1)
        command = ""

        while self.start_date <= self.end_date:
            try:
                """NetCDF generation and logs"""
                self.info_log(
                    "Initiating pypam/pbp processing sequence for audio file associated with : "
                    + str(self.start_date)
                )
                self.info_log(
                    "Initiating metadata generation associated with : "
                    + str(self.start_date)
                )

                if self.recorder == "SOUNDTRAP":
                    command = self.synth_pbp_hmb_gen(
                        date=self.start_date.strftime("%Y%m%d"),
                        json_base_dir=self.json_base_dir,
                        audio_base_dir=self.uri,
                        output_dir=self.nc_output_dir,
                        global_attrs=self.global_attrs,
                        variable_attrs=self.variable_attrs,
                        output_prefix=self.output_prefix,
                        sensitivity_flat_value=self.sensitivity_flat_value,
                        sensitivity_uri=None,
                        voltage_multiplier=None,
                        subset_to=self.subset_to,
                    )
                if self.recorder == "NRS":
                    command = self.synth_pbp_hmb_gen(
                        date=self.start_date.strftime("%Y%m%d"),
                        json_base_dir=self.json_base_dir,
                        audio_base_dir=self.uri,
                        output_dir=self.nc_output_dir,
                        global_attrs=self.global_attrs,
                        variable_attrs=self.variable_attrs,
                        output_prefix=self.output_prefix,
                        sensitivity_flat_value=None,
                        sensitivity_uri=self.sensitivity_uri,
                        voltage_multiplier=self.voltage_multiplier,
                        subset_to=self.subset_to,
                    )
                logger.bind(name=self.name).opt(colors=True).info(
                    "<blue>Checking if netCDF file associated with "
                    + str(self.start_date.strftime("%Y%m%d"))
                    + " exists...</blue>"
                )
                if not self.search_filenames(
                    self.nc_output_dir, str(self.start_date.strftime("%Y%m%d")) + ".nc"
                ):
                    logger.bind(name=self.name).opt(colors=True).info(
                        "<blue>No netCDF file exists for "
                        + str(self.start_date)
                        + ". Proceeding to netCDF generation of "
                        + str(self.start_date)
                        + "."
                        + "</blue>"
                    )
                    logger.bind(name=self.name).opt(colors=True).info(
                        "<blue>Proceeding to netCDF generatrion...</blue>"
                    )
                    logger.bind(name=self.name).opt(colors=True).info(
                        "<green>running > " + command + "</green>"
                    )

                    os.system(command)

                    logger.bind(name=self.name).opt(colors=True).info(
                        "<blue>NetCDF file generation for "
                        + str(self.start_date)
                        + " complete!</blue>"
                    )
                else:
                    logger.bind(name=self.name).opt(colors=True).info(
                        "<yellow>NetCDF file already exists for "
                        + str(self.start_date)
                        + "</yellow>"
                    )

                """NetCDF Plotting"""
                command = ""  # Reset command
                if os.name == "nt":  # For Windows-based systems
                    command = self.synth_pbp_plot_gen(
                        latlon=self.latlon,
                        title=self.title,
                        cmlim=self.cmlim,
                        ylim=self.ylim,
                        nc_file=os.path.join(
                            self.nc_output_dir,
                            self.output_prefix
                            + str(self.start_date.strftime("%Y%m%d"))
                            + ".nc",
                        ),
                    )  # Generate the command for plotting the NetCDF file
                if os.name == "posix":  # For Unix-based systems
                    command = self.synth_pbp_plot_gen(
                        latlon=self.latlon,
                        title=self.title,
                        cmlim=self.cmlim,
                        ylim=self.ylim,
                        nc_file=os.path.join(
                            self.nc_output_dir,
                            self.output_prefix
                            + str(self.start_date.strftime("%Y%m%d"))
                            + ".nc",
                        ),
                    )  # Generate the command for plotting the NetCDF file

                logger.bind(name=self.name).opt(colors=True).info(
                    "<blue>Initiating plot generation for audio file associated with date : "
                    + str(self.start_date)
                    + "</blue>"
                )
                logger.bind(name=self.name).opt(colors=True).info(
                    "<blue>Checking if jpg file associated with "
                    + str(self.start_date)
                    + " exists...</blue>"
                )
                if not self.search_filenames(
                    self.nc_output_dir, str(self.start_date.strftime("%Y%m%d")) + ".jpg"
                ):
                    logger.bind(name=self.name).opt(colors=True).info(
                        "<blue>No plot exists or has been generated for the date: "
                        + str(self.start_date)
                        + "</blue>"
                    )
                    logger.bind(name=self.name).opt(colors=True).info(
                        "<blue>Proceeding to plot generatrion from netCDF...</blue>"
                    )
                    logger.bind(name=self.name).opt(colors=True).info(
                        "<green>running > " + command + "</green>"
                    )
                    os.system(command)
                else:
                    logger.bind(name=self.name).opt(colors=True).info(
                        "<yellow>Plot already exists for "
                        + str(self.start_date)
                        + "</yellow>"
                    )
                    logger.bind(name=self.name).opt(colors=True).info(
                        "<yellow>Performing an override of the existing plot for "
                        + str(self.start_date)
                        + "</yellow>"
                    )
                    logger.bind(name=self.name).opt(colors=True).info(
                        "<green>running > " + command + "</green>"
                    )
                    os.system(command)
                    logger.bind(name=self.name).opt(colors=True).info(
                        "<blue>Plot generation complete!</blue>"
                    )

                self.start_date += delta  # Iterate to next day.
                time.sleep(1)

            except TypeError as e:
                logger.bind(name=self.name).error(
                    f"Error: {e} at line {sys.exc_info()[-1].tb_lineno} ; Processing was unsuccessful for {self.start_date}"
                )
