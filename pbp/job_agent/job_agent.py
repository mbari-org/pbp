

from pathlib import Path
from datetime import date, timedelta, datetime
import os
import time
from loguru import logger  # A great logger option.


    

class JobAgent:
    """This class structure is designed to encapsulate the entire pbp process suite in a simple agent that performs all tasks, more automation with fewer parameters and no URI interface."""

    def __init__(
        self,
        recorder,  # Recorder type
        audio_base_dir,  # Audio base directory
        json_base_dir,  # JSON base directory
        xml_dir,  # XML directory
        start,  # Start date
        end,  # End date
        prefix,  # Prefix
        nc_output_dir,  # NetCDF output directory
        global_attrs_file,  # Global attributes file
        variable_attrs_file,  # Variable attributes file
        sensitivity_flat_value,  # Sensitivity flat value
        latlon,  # Latitude and Longitude
        title,  # Title
        cmlim,  # CMLIM
        ylim,  # YLIM
        log_dir # Log directory
    ):
        self.recorder = recorder
        self.audio_base_dir = audio_base_dir

        if os.name == "nt":
            self.uri = r"file:\\\ " + audio_base_dir
            self.uri = self.uri.replace(" ", "")
            path = Path(self.uri)
        else:
            self.uri = r"file:/// " + audio_base_dir
            self.uri = self.uri.replace(" ", "")
            path = Path(self.uri)

        self.meta_log_output_dir = json_base_dir
        self.json_base_dir = json_base_dir
        self.xml_dir = xml_dir

        self.prefix = prefix

        self.nc_output_dir = nc_output_dir
        self.start_date = datetime.strptime(start, "%Y%m%d").date()
        self.end_date = datetime.strptime(end, "%Y%m%d").date()

        if os.name == "nt":  # For Windows-based systems
            self.global_attrs_file = (
                r"file:\\\ " + global_attrs_file
            )  # Apply URI formatting
            self.global_attrs_file = self.global_attrs_file.replace(
                " ", ""
            )  # Remove any spaces. This is to avoid the escape character issue in python.
            self.variable_attrs_file = (
                r"file:\\\ " + variable_attrs_file
            )  # Apply URI formatting
            self.variable_attrs_file = self.variable_attrs_file.replace(
                " ", ""
            )  # Remove any spaces. This is to avoid the escape character issue in python.
        else:  # For Unix-based systems
            self.global_attrs_file = (
                r"file:/// " + global_attrs_file
            )  # Apply URI formatting
            self.global_attrs_file = self.global_attrs_file.replace(
                " ", ""
            )  # Remove any spaces. This is to avoid the escape character issue in python.
            self.variable_attrs_file = (
                r"file:/// " + variable_attrs_file
            )  # Apply URI formatting
            self.variable_attrs_file = self.variable_attrs_file.replace(
                " ", ""
            )  # Remove any spaces. This is to avoid the escape character issue in python.

        self.sensitivity_flat_value = sensitivity_flat_value
        self.latlon = latlon
        self.title = title
        self.cmlim = cmlim
        self.ylim = ylim  # YLIM
        self.orch_dir = log_dir
        #logger.add(log_dir+r"\process-orchestration.log")
        self.output_prefix = self.deployment+"_"

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
        self, recorder, uri, output_dir, json_base_dir, xml_dir, start, end, prefix
    ):
        command = (
            r"pbp-meta-gen "
            + r"--recorder "
            + recorder
            + r" --uri "
            + uri
            + r" --output-dir "
            + output_dir
            + r" --json-base-dir "
            + json_base_dir
            + r" --xml-dir "
            + xml_dir
            + r" --start "
            + start
            + r" --end "
            + end
            + r" --prefix "
            + str(prefix)
        )
        return command

    def synth_pbp_hmb_gen(
        self,
        date,
        json_base_dir,
        audio_base_dir,
        output_dir,
        global_attrs,
        variable_attrs,
        sensitivity_flat_value,
        output_prefix
    ):
        command = (
            r"pbp-hmb-gen --date "
            + date
            + r" --json-base-dir "
            + json_base_dir
            + r" --audio-base-dir "
            + audio_base_dir
            + r" --output-dir "
            + output_dir
            + r" --global-attrs "
            + global_attrs
            + r" --variable-attrs "
            + variable_attrs
            + r" --sensitivity-flat-value "
            + sensitivity_flat_value
            + r" --output-prefix "
            + output_prefix
        )
        return command

    def synth_pbp_plot_gen(self, latlon, title, cmlim, ylim, nc_file):
        command = (
            r"pbp-hmb-plot --latlon "
            + latlon
            + r" --title "
            + title
            + r" --cmlim "
            + cmlim
            + r" --ylim "
            + ylim
            + r" "
            + nc_file
        )
        return command

    def run(self):
        logger.opt(colors=True).info(
            "<blue>Initializing the pbp/pypam processing suite.</blue>"
        )

        """Metadata generation and logs"""

        command = self.synth_pbp_meta_gen(
            self.recorder,
            self.uri,
            self.meta_log_output_dir,
            self.json_base_dir,
            self.xml_dir,
            self.start_date.strftime("%Y%m%d"),
            self.end_date.strftime("%Y%m%d"),
            self.prefix,
        )
        logger.opt(colors=True).info(
            "<blue>Initiating processing for audio file and netCDF generation associated with : "
            + str(self.start_date)
            + "</blue>"
        )
        logger.opt(colors=True).info("<green>running > " + command + "</green>")
        os.system(command)

        delta = timedelta(days=1)
        command = ""

        while self.start_date <= self.end_date:
            try:
                """NetCDF generation and logs"""

                logger.opt(colors=True).info(
                    "<blue>Initiating pypam/pbp processing sequence for audio file associated with : "
                    + str(self.start_date)
                    + "</blue>"
                )
                logger.opt(colors=True).info(
                    "<blue>Initiating metadata generation associated with : "
                    + str(self.start_date)
                    + "</blue>"
                )
                command = self.synth_pbp_hmb_gen(
                    date=self.start_date.strftime("%Y%m%d"),
                    json_base_dir=self.json_base_dir,
                    audio_base_dir=self.audio_base_dir,
                    output_dir=self.nc_output_dir,
                    global_attrs=self.global_attrs_file,
                    variable_attrs=self.variable_attrs_file,
                    sensitivity_flat_value=self.sensitivity_flat_value,
                    output_prefix = self.output_prefix
                )

                logger.opt(colors=True).info(
                    "<blue>Checking if netCDF file associated with "
                    + str(self.start_date.strftime("%Y%m%d"))
                    + " exists...</blue>"
                )
                if not self.search_filenames(
                    self.nc_output_dir, str(self.start_date.strftime("%Y%m%d")) + ".nc"
                ):
                    logger.opt(colors=True).info(
                        "<blue>No netCDF file exists for "
                        + str(self.start_date) + ". Proceeding to netCDF generation of "+str(self.start_date)+"."
                        + "</blue>"
                    )
                    logger.opt(colors=True).info(
                        "<blue>Proceeding to netCDF generatrion...</blue>"
                    )
                    logger.opt(colors=True).info(
                        "<green>running > " + command + "</green>"
                    )
                    
                    os.system(command)
                    
                    logger.opt(colors=True).info(
                        "<blue>NetCDF file generation for "
                        + str(self.start_date)
                        + " complete!</blue>"
                    )
                else:
                    logger.opt(colors=True).info(
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
                        nc_file=self.nc_output_dir
                        + r"\milli_psd_"
                        + str(self.start_date.strftime("%Y%m%d"))
                        + ".nc",
                    )  # Generate the command for plotting the NetCDF file
                else:  # For Unix-based systems
                    command = self.synth_pbp_plot_gen(
                        latlon=self.latlon,
                        title=self.title,
                        cmlim=self.cmlim,
                        ylim=self.ylim,
                        nc_file=self.nc_output_dir
                        + self.output_prefix+r"/milli_psd_"
                        + str(self.start_date.strftime("%Y%m%d"))
                        + ".nc",
                    )  # Generate the command for plotting the NetCDF file

                logger.opt(colors=True).info(
                    "<blue>Initiating plot generation for audio file associated with date : "
                    + str(self.start_date)
                    + "</blue>"
                )
                logger.opt(colors=True).info(
                    "<blue>Checking if jpg file associated with "
                    + str(self.start_date)
                    + " exists...</blue>"
                )
                if not self.search_filenames(
                    self.nc_output_dir, str(self.start_date.strftime("%Y%m%d")) + ".jpg"
                ):
                    logger.opt(colors=True).info(
                        "<blue>No plot exists or has been generated for the date: "
                        + str(self.start_date)
                        + "</blue>"
                    )
                    logger.opt(colors=True).info(
                        "<blue>Proceeding to plot generatrion from netCDF...</blue>"
                    )
                    logger.opt(colors=True).info(
                        "<green>running > " + command + "</green>"
                    )
                    os.system(command)
                else:
                    logger.opt(colors=True).info(
                        "<yellow>Plot already exists for "
                        + str(self.start_date)
                        + "</yellow>"
                    )
                    logger.opt(colors=True).info(
                        "<yellow>Perfroming an override of the existing plot for "
                        + str(self.start_date)
                        + "</yellow>"
                    )
                    logger.opt(colors=True).info(
                        "<green>running > " + command + "</green>"
                    )
                    os.system(command)
                    logger.opt(colors=True).info(
                    "<blue>Plot generation complete!</blue>"
                )

                self.start_date += delta  # Iterate to next day.
                logger.opt(colors=True).info(
                    "<blue>Proceeding to the next day for processing...</blue>"
                )
                time.sleep(1)

            except TypeError as e:
                logger.error("Processing was unsucessful for " + str(self.start_date))
                logger.error(e)