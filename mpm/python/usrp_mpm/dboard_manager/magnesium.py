#
# Copyright 2017 Ettus Research (National Instruments)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
magnesium dboard implementation module
"""

from __future__ import print_function
import os
import time
import threading
from six import iterkeys, iteritems
from . import lib # Pulls in everything from C++-land
from .base import DboardManagerBase
from .. import nijesdcore
from ..uio import UIO
from ..mpmlog import get_logger
from .lmk_mg import LMK04828Mg
from usrp_mpm.periph_manager.udev import get_eeprom_paths
from usrp_mpm.cores import ClockSynchronizer
from ..sysfs_gpio import SysFSGPIO
from usrp_mpm.bfrfs import BufferFS
from usrp_mpm.mpmutils import poll_with_timeout

def create_spidev_iface(dev_node):
    """
    Create a regs iface from a spidev node
    """
    SPI_SPEED_HZ = 1000000
    SPI_MODE = 3
    SPI_ADDR_SHIFT = 8
    SPI_DATA_SHIFT = 0
    SPI_READ_FLAG = 1<<23
    SPI_WRIT_FLAG = 0
    return lib.spi.make_spidev_regs_iface(
        dev_node,
        SPI_SPEED_HZ,
        SPI_MODE,
        SPI_ADDR_SHIFT,
        SPI_DATA_SHIFT,
        SPI_READ_FLAG,
        SPI_WRIT_FLAG
    )

def create_spidev_iface_cpld(dev_node):
    """
    Create a regs iface from a spidev node
    """
    SPI_SPEED_HZ = 1000000
    SPI_MODE = 0
    SPI_ADDR_SHIFT = 16
    SPI_DATA_SHIFT = 0
    SPI_READ_FLAG = 1<<23
    SPI_WRIT_FLAG = 0
    return lib.spi.make_spidev_regs_iface(
        dev_node,
        SPI_SPEED_HZ,
        SPI_MODE,
        SPI_ADDR_SHIFT,
        SPI_DATA_SHIFT,
        SPI_READ_FLAG,
        SPI_WRIT_FLAG
    )

def create_spidev_iface_phasedac(dev_node):
    """
    Create a regs iface from a spidev node (ADS5681)
    """
    return lib.spi.make_spidev_regs_iface(
        str(dev_node),
        1000000, # Speed (Hz)
        1, # SPI mode
        16, # Addr shift
        0, # Data shift
        0, # Read flag
        0, # Write flag
    )

###############################################################################
# Peripherals
###############################################################################
class TCA6408(object):
    """
    Abstraction layer for the port/gpio expander
    """
    pins = (
        'PWR-GOOD-3.6V', #3.6V
        'PWR-EN-3.6V',   #3.6V
        'PWR-GOOD-1.5V', #1.5V
        'PWR-EN-1.5V',   #1.5V
        'PWR-GOOD-5.5V', #5.5V
        'PWR-EN-5.5V',   #5.5V
        '6',
        'LED',
    )

    def __init__(self, i2c_dev):
        if i2c_dev is None:
            raise RuntimeError("Need to specify i2c device to use the TCA6408")
        self._gpios = SysFSGPIO('tca6408', 0xBF, 0xAA, 0xAA, i2c_dev)

    def set(self, name, value=None):
        """
        Assert a pin by name
        """
        assert name in self.pins
        self._gpios.set(self.pins.index(name), value=value)

    def reset(self, name):
        """
        Deassert a pin by name
        """
        self.set(name, value=0)

    def get(self, name):
        """
        Read back a pin by name
        """
        assert name in self.pins
        return self._gpios.get(self.pins.index(name))

class DboardClockControl(object):
    """
    Control the FPGA MMCM for Radio Clock control.
    """
    # Clocking Register address constants
    RADIO_CLK_MMCM      = 0x0020
    PHASE_SHIFT_CONTROL = 0x0024
    RADIO_CLK_ENABLES   = 0x0028
    MGT_REF_CLK_STATUS  = 0x0030

    def __init__(self, regs, log):
        self.log = log
        self.regs = regs
        self.poke32 = self.regs.poke32
        self.peek32 = self.regs.peek32

    def enable_outputs(self, enable=True):
        """
        Enables or disables the MMCM outputs.
        """
        if enable:
            self.poke32(self.RADIO_CLK_ENABLES, 0x011)
        else:
            self.poke32(self.RADIO_CLK_ENABLES, 0x000)

    def reset_mmcm(self):
        """
        Uninitialize and reset the MMCM
        """
        self.log.trace("Disabling all Radio Clocks, then resetting MMCM...")
        self.enable_outputs(False)
        self.poke32(self.RADIO_CLK_MMCM, 0x1)

    def enable_mmcm(self):
        """
        Unreset MMCM and poll lock indicators

        If MMCM is not locked after unreset, an exception is thrown.
        """
        self.log.trace("Un-resetting MMCM...")
        self.poke32(self.RADIO_CLK_MMCM, 0x2)
        if not poll_with_timeout(
                lambda: bool(self.peek32(self.RADIO_CLK_MMCM) & 0x10),
                500,
                10,
            ):
            self.log.error("MMCM not locked!")
            raise RuntimeError("MMCM not locked!")
        self.log.trace("MMCM locked. Enabling output MMCM clocks...")
        self.enable_outputs(True)

    def check_refclk(self):
        """
        Not technically a clocking reg, but related.
        """
        return bool(self.peek32(self.MGT_REF_CLK_STATUS) & 0x1)

class MgCPLD(object):
    """
    Control class for the CPLD
    """
    CPLD_SIGNATURE = 0xCAFE # Expected signature ("magic number")
    CPLD_REV = 4

    REG_SIGNATURE = 0x0000
    REG_REVISION = 0x0001
    REG_OLDEST_COMPAT = 0x0002
    REG_BUILD_CODE_LSB = 0x0003
    REG_BUILD_CODE_MSB = 0x0004
    REG_SCRATCH = 0x0005
    REG_CPLD_CTRL = 0x0010
    REG_LMK_CTRL = 0x0011
    REG_LO_STATUS = 0x0012
    REG_MYK_CTRL = 0x0013

    def __init__(self, regs, log):
        self.log = log.getChild("CPLD")
        self.log.debug("Initializing CPLD...")
        self.regs = regs
        self.poke16 = self.regs.poke16
        self.peek16 = self.regs.peek16
        signature = self.peek16(self.REG_SIGNATURE)
        if signature != self.CPLD_SIGNATURE:
            self.log.error(
                "CPLD Signature Mismatch! " \
                "Expected: 0x{:04X} Got: 0x{:04X}".format(
                    self.CPLD_SIGNATURE, signature))
            raise RuntimeError("CPLD Status Check Failed!")
        rev = self.peek16(self.REG_REVISION)
        if rev != self.CPLD_REV:
            self.log.error("CPLD Revision Mismatch! " \
                           "Expected: %d Got: %d", self.CPLD_REV, rev)
            raise RuntimeError("CPLD Revision Check Failed!")
        date_code = self.peek16(self.REG_BUILD_CODE_LSB) | \
                    (self.peek16(self.REG_BUILD_CODE_MSB) << 16)
        self.log.trace(
            "CPLD Signature: 0x{:X} Revision: 0x{:04X} Date code: 0x{:08X}"
            .format(signature, rev, date_code))

    def set_scratch(self, val):
        " Write to the scratch register "
        self.poke16(self.REG_SCRATCH, val & 0xFFFF)

    def get_scratch(self):
        " Read from the scratch register "
        return self.peek16(self.REG_SCRATCH)

    def reset(self):
        " Reset entire CPLD "
        self.log.trace("Resetting CPLD...")
        self.poke16(self.REG_CPLD_CTRL, 0x1)
        self.poke16(self.REG_CPLD_CTRL, 0x0)

    def set_pdac_control(self, enb):
        """
        If enb is True, the Phase DAC will exclusively control the VCXO voltage
        """
        self.log.trace("Giving Phase %s control over VCXO voltage...",
                       "exclusive" if bool(enb) else "non-exclusive")
        reg_val = (1<<4) if enb else 0
        self.poke16(self.REG_LMK_CTRL, reg_val)

    def get_lo_lock_status(self, which):
        """
        Returns True if the 'which' LO is locked. 'which' is either 'tx' or
        'rx'.
        """
        mask = (1<<4) if which.lower() == 'tx' else 1
        return bool(self.peek16(self.REG_LO_STATUS & mask))

    def reset_mykonos(self):
        """
        Hard-resets Mykonos
        """
        self.log.debug("Resetting AD9371!")
        self.poke16(self.REG_MYK_CTRL, 0x1)
        time.sleep(0.001) # No spec here, but give it some time to reset.
        self.poke16(self.REG_MYK_CTRL, 0x0)
        time.sleep(0.001) # No spec here, but give it some time to reset.


###############################################################################
# Main dboard control class
###############################################################################
class Magnesium(DboardManagerBase):
    """
    Holds all dboard specific information and methods of the magnesium dboard
    """
    #########################################################################
    # Overridables
    #
    # See DboardManagerBase for documentation on these fields
    #########################################################################
    pids = [0x150]
    #file system path to i2c-adapter/mux
    base_i2c_adapter = '/sys/class/i2c-adapter'
    # Maps the chipselects to the corresponding devices:
    spi_chipselect = {"cpld": 0, "lmk": 1, "mykonos": 2, "phase_dac": 3}
    @staticmethod
    def list_required_dt_overlays(eeprom_md, sfp_config, device_args):
        """
        Lists device tree overlays that need to be applied before this class can
        be used. List of strings.
        Are applied in order.

        eeprom_md -- Dictionary of info read out from the dboard EEPROM
        sfp_config -- A string identifying the configuration of the SFP ports.
                      Example: "XG", "HG", "XA", ...
        device_args -- Arbitrary dictionary of info, typically user-defined
        """
        return ['magnesium-{sfp}'.format(sfp=sfp_config)]
    ### End of overridables #################################################
    # Class-specific, but constant settings:
    spi_factories = {
        "cpld": create_spidev_iface_cpld,
        "lmk": create_spidev_iface,
        "mykonos": create_spidev_iface,
        "phase_dac": create_spidev_iface_phasedac,
    }
    # Map I2C channel to slot index
    i2c_chan_map = {0: 'i2c-9', 1: 'i2c-10'}
    user_eeprom = {
        2: { # RevC
            'label': "e0004000.i2c",
            'offset': 1024,
            'max_size': 32786 - 1024,
            'alignment': 1024,
        },
    }
    # DAC is initialized to midscale automatically on power-on: 16-bit DAC, so midpoint
    # is at 2^15 = 32768. However, the linearity of the DAC is best just below that
    # point, so we set it to the (carefully calculated) alternate value instead.
    INIT_PHASE_DAC_WORD = 31000 # Intentionally decimal

    def __init__(self, slot_idx, **kwargs):
        super(Magnesium, self).__init__(slot_idx, **kwargs)
        self.log = get_logger("Magnesium-{}".format(slot_idx))
        self.log.trace("Initializing Magnesium daughterboard, slot index %d",
                       self.slot_idx)
        self.rev = int(self.device_info['rev'])
        self.log.trace("This is a rev: {}".format(chr(65 + self.rev)))
        # This is a default ref clock freq, it must be updated before init() is
        # called!
        self.ref_clock_freq = 10e6
        self.master_clock_freq = 125e6 # Same
        # Initialize power and peripherals that don't need user-settings
        self._port_expander = TCA6408(self._get_i2c_dev(self.slot_idx))
        self._power_on()
        self.log.debug("Loading C++ drivers...")
        self._device = lib.dboards.magnesium_manager(
            self._spi_nodes['mykonos'],
        )
        self.mykonos = self._device.get_radio_ctrl()
        self.spi_lock = self._device.get_spi_lock()
        self.log.trace("Loaded C++ drivers.")
        self._init_myk_api(self.mykonos)
        self.eeprom_fs, self.eeprom_path = self._init_user_eeprom(
            self.user_eeprom[self.rev]
        )
        self.radio_regs = UIO(
            label="dboard-regs-{}".format(self.slot_idx),
            read_only=False
        )
        self.log.trace("Loading SPI devices...")
        self._spi_ifaces = {
            key: self.spi_factories[key](self._spi_nodes[key])
            for key in self._spi_nodes
        }
        self.cpld = MgCPLD(self._spi_ifaces['cpld'], self.log)
        self.dboard_clk_control = DboardClockControl(self.radio_regs, self.log)
        # Declare some attributes to make linter happy:
        self.lmk = None
        self.clock_synchronizer = None
        self.jesdcore = None

    def _power_on(self):
        " Turn on power to daughterboard "
        self.log.trace("Powering on slot_idx={}...".format(self.slot_idx))
        self._port_expander.set("PWR-EN-3.6V")
        self._port_expander.set("PWR-EN-1.5V")
        self._port_expander.set("PWR-EN-5.5V")
        self._port_expander.set("LED")

    def _power_off(self):
        " Turn off power to daughterboard "
        self.log.trace("Powering off slot_idx={}...".format(self.slot_idx))
        self._port_expander.reset("PWR-EN-3.6V")
        self._port_expander.reset("PWR-EN-1.5V")
        self._port_expander.reset("PWR-EN-5.5V")
        self._port_expander.reset("LED")

    def _get_i2c_dev(self, slot_idx):
        " Return the I2C path for this daughterboard "
        import pyudev
        context = pyudev.Context()
        i2c_dev_path = os.path.join(
            self.base_i2c_adapter,
            self.i2c_chan_map[slot_idx]
        )
        return pyudev.Devices.from_sys_path(context, i2c_dev_path)

    def _init_myk_api(self, myk):
        """
        Propagate the C++ Mykonos API into Python land.
        """
        def export_method(obj, method):
            " Export a method object, including docstring "
            meth_obj = getattr(obj, method)
            def func(*args):
                " Functor for storing docstring too "
                return meth_obj(*args)
            func.__doc__ = meth_obj.__doc__
            return func
        self.log.trace("Forwarding AD9371 methods to Magnesium class...")
        for method in [
                x for x in dir(self.mykonos)
                if not x.startswith("_") and \
                        callable(getattr(self.mykonos, x))]:
            self.log.trace("adding {}".format(method))
            setattr(self, method, export_method(myk, method))

    def _init_user_eeprom(self, eeprom_info):
        """
        Reads out user-data EEPROM, and intializes a BufferFS object from that.
        """
        self.log.trace("Initializing EEPROM user data...")
        eeprom_paths = get_eeprom_paths(eeprom_info.get('label'))
        self.log.trace("Found the following EEPROM paths: `{}'".format(
            eeprom_paths))
        eeprom_path = eeprom_paths[self.slot_idx]
        self.log.trace("Selected EEPROM path: `{}'".format(eeprom_path))
        user_eeprom_offset = eeprom_info.get('offset', 0)
        self.log.trace("Selected EEPROM offset: %d", user_eeprom_offset)
        user_eeprom_data = open(eeprom_path, 'rb').read()[user_eeprom_offset:]
        self.log.trace("Total EEPROM size is: %d bytes", len(user_eeprom_data))
        # FIXME verify EEPROM sectors
        return BufferFS(
            user_eeprom_data,
            max_size=eeprom_info.get('max_size'),
            alignment=eeprom_info.get('alignment', 1024),
            log=self.log
        ), eeprom_path


    def init(self, args):
        """
        Execute necessary init dance to bring up dboard
        """
        def _init_lmk(lmk_spi, ref_clk_freq,
                      pdac_spi, init_phase_dac_word):
            """
            Sets the phase DAC to initial value, and then brings up the LMK
            according to the selected ref clock frequency.
            Will throw if something fails.
            """
            self.log.trace("Initializing Phase DAC to d{}.".format(
                init_phase_dac_word
            ))
            pdac_spi.poke16(0x0, init_phase_dac_word)
            return LMK04828Mg(lmk_spi, self.spi_lock, ref_clk_freq, self.log)
        def _sync_db_clock(synchronizer):
            " Synchronizes the DB clock to the common reference "
            synchronizer.run_sync(measurement_only=False)
            offset_error = synchronizer.run_sync(measurement_only=True)
            if offset_error > 100e-12:
                self.log.error("Clock synchronizer measured an offset of {:.1f} ps!".format(
                    offset_error*1e12
                ))
                raise RuntimeError("Clock synchronizer measured an offset of {:.1f} ps!".format(
                    offset_error*1e12
                ))
            else:
                self.log.debug("Residual DAC offset error: {:.1f} ps.".format(
                    offset_error*1e12
                ))
            self.log.info("Sample Clock Synchronization Complete!")
        ## Go, go, go!
        self.log.info("init() called with args `{}'".format(
            ",".join(['{}={}'.format(x, args[x]) for x in args])
        ))
        self.dboard_clk_control.reset_mmcm()
        self.lmk = _init_lmk(
            self._spi_ifaces['lmk'],
            self.ref_clock_freq,
            self._spi_ifaces['phase_dac'],
            self.INIT_PHASE_DAC_WORD,
        )
        self.dboard_clk_control.enable_mmcm()
        self.log.info("Sample Clocks and Phase DAC Configured Successfully!")
        # Synchronize DB Clocks
        self.clock_synchronizer = ClockSynchronizer(
            self.radio_regs,
            self.dboard_clk_control,
            self.lmk,
            self._spi_ifaces['phase_dac'],
            0, # TODO this might not actually be zero
            self.master_clock_freq,
            self.ref_clock_freq,
            860E-15, # TODO don't hardcode. This should live in the EEPROM
            self.INIT_PHASE_DAC_WORD,
            3e9,         # lmk_vco_freq
            [128e-9,],   # target_values
            0x0,         # spi_addr TODO: make this a constant and replace in _sync_db_clock as well
            self.log
        )
        _sync_db_clock(self.clock_synchronizer)
        # Clocks and PPS are now fully active!

        self.init_jesd(self.radio_regs)
        self.mykonos.start_radio()
        return True


    def cpld_peek(self, addr):
        """
        Debug for accessing the CPLD via the RPC shell.
        """
        return self.cpld.peek16(addr)

    def cpld_poke(self, addr, data):
        """
        Debug for accessing the CPLD via the RPC shell.
        """
        self.cpld.poke16(addr, data)
        return self.cpld.peek16(addr)

    def init_jesd(self, uio):
        """
        Bring up the JESD link between Mykonos and the N310.
        """
        # CPLD Register Definition
        self.log.trace("Creating jesdcore object")
        self.jesdcore = nijesdcore.NIMgJESDCore(uio, self.slot_idx)
        self.jesdcore.check_core()
        self.jesdcore.unreset_qpll()
        self.jesdcore.init()

        self.log.trace("Pulsing Mykonos Hard Reset...")
        self.cpld.reset_mykonos()
        self.log.trace("Initializing Mykonos...")
        self.mykonos.begin_initialization()
        # Multi-chip Sync requires two SYSREF pulses at least 17us apart.
        self.jesdcore.send_sysref_pulse()
        time.sleep(0.001)
        self.jesdcore.send_sysref_pulse()
        self.mykonos.finish_initialization()

        self.log.trace("Starting JESD204b Link Initialization...")
        # Generally, enable the source before the sink. Start with the DAC side.
        self.log.trace("Starting FPGA framer...")
        self.jesdcore.init_framer()
        self.log.trace("Starting Mykonos deframer...")
        self.mykonos.start_jesd_rx()
        # Now for the ADC link. Note that the Mykonos framer will not start issuing CGS
        # characters until SYSREF is received by the framer. Therefore we enable the
        # framer in Mykonos and the FPGA, send a SYSREF pulse to everyone, and then
        # start the deframer in the FPGA.
        self.log.trace("Starting Mykonos framer...")
        self.mykonos.start_jesd_tx()
        self.log.trace("Enable FPGA SYSREF Receiver.")
        self.jesdcore.enable_lmfc()
        self.jesdcore.send_sysref_pulse()
        self.log.trace("Starting FPGA deframer...")
        self.jesdcore.init_deframer()

        # Allow a bit of time for CGS/ILA to complete.
        time.sleep(0.100)

        if not self.jesdcore.get_framer_status():
            self.log.error("FPGA Framer Error!")
            raise Exception('JESD Core Framer is not synced!')
        if (self.mykonos.get_deframer_status() & 0x7F) != 0x28:
            self.log.error("Mykonos Deframer Error: 0x{:X}".format((self.mykonos.get_deframer_status() & 0x7F)))
            raise Exception('Mykonos Deframer is not synced!')
        if not self.jesdcore.get_deframer_status():
            self.log.error("FPGA Deframer Error!")
            raise Exception('JESD Core Deframer is not synced!')
        if (self.mykonos.get_framer_status() & 0xFF) != 0x3E:
            self.log.error("Mykonos Framer Error: 0x{:X}".format((self.mykonos.get_framer_status() & 0xFF)))
            raise Exception('Mykonos Framer is not synced!')
        if (self.mykonos.get_multichip_sync_status() & 0xB) != 0xB:
            raise Exception('Mykonos multi chip sync failed!')
        self.log.info("JESD204B Link Initialization & Training Complete")


    def dump_jesd_core(self):
        " Debug method to dump all JESD core regs "
        radio_regs = UIO(label="dboard-regs-{}".format(self.slot_idx))
        for i in range(0x2000, 0x2110, 0x10):
            print(("0x%04X " % i), end=' ')
            for j in range(0, 0x10, 0x4):
                print(("%08X" % radio_regs.peek32(i + j)), end=' ')
            print("")

    def get_user_eeprom_data(self):
        """
        Return a dict of blobs stored in the user data section of the EEPROM.
        """
        return {
            blob_id: self.eeprom_fs.get_blob(blob_id)
            for blob_id in iterkeys(self.eeprom_fs.entries)
        }

    def set_user_eeprom_data(self, eeprom_data):
        """
        Update the local EEPROM with the data from eeprom_data.

        The actual writing to EEPROM can take some time, and is thus kicked
        into a background task. Don't call set_user_eeprom_data() quickly in
        succession. Also, while the background task is running, reading the
        EEPROM is unavailable and MPM won't be able to reboot until it's
        completed.
        However, get_user_eeprom_data() will immediately return the correct
        data after this method returns.
        """
        for blob_id, blob in iteritems(eeprom_data):
            self.eeprom_fs.set_blob(blob_id, blob)
        self.log.trace("Writing EEPROM info to `{}'".format(self.eeprom_path))
        eeprom_offset = self.user_eeprom[self.rev]['offset']
        def _write_to_eeprom_task(path, offset, data, log):
            " Writer task: Actually write to file "
            # Note: This can be sped up by only writing sectors that actually
            # changed. To do so, this function would need to read out the
            # current state of the file, do some kind of diff, and then seek()
            # to the different sectors. When very large blobs are being
            # written, it doesn't actually help all that much, of course,
            # because in that case, we'd anyway be changing most of the EEPROM.
            with open(path, 'r+b') as eeprom_file:
                log.trace("Seeking forward to `{}'".format(offset))
                eeprom_file.seek(eeprom_offset)
                log.trace("Writing a total of {} bytes.".format(
                    len(self.eeprom_fs.buffer)))
                eeprom_file.write(data)
                log.trace("EEPROM write complete.")
        thread_id = "eeprom_writer_task_{}".format(self.slot_idx)
        if any([x.name == thread_id for x in threading.enumerate()]):
            # Should this be fatal?
            self.log.warn("Another EEPROM writer thread is already active!")
        writer_task = threading.Thread(
            target=_write_to_eeprom_task,
            args=(
                self.eeprom_path,
                eeprom_offset,
                self.eeprom_fs.buffer,
                self.log
            ),
            name=thread_id,
        )
        writer_task.start()
        # Now return and let the copy finish on its own. The thread will detach
        # and MPM won't terminate this process until the thread is complete.
        # This does not stop anyone from killing this process (and the thread)
        # while the EEPROM write is happening, though.


    ##########################################################################
    # Sensors
    ##########################################################################
    def get_lowband_lo_lock(self, which):
        """
        Return LO lock status (Boolean!) of the lowband LOs. 'which' must be
        either 'tx' or 'rx'
        """
        assert which.lower() in ('tx', 'rx')
        return self.cpld.get_lo_lock_status(which)

