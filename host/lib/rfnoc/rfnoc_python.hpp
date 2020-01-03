//
// Copyright 2019 Ettus Research, a National Instruments Brand
//
// SPDX-License-Identifier: GPL-3.0-or-later
//

#ifndef INCLUDED_UHD_RFNOC_PYTHON_HPP
#define INCLUDED_UHD_RFNOC_PYTHON_HPP

#include "../stream_python.hpp"
#include <uhd/rfnoc/block_id.hpp>
#include <uhd/rfnoc/graph_edge.hpp>
#include <uhd/rfnoc/mb_controller.hpp>
#include <uhd/rfnoc/noc_block_base.hpp>
#include <uhd/rfnoc_graph.hpp>
#include <uhd/transport/adapter_id.hpp>
#include <uhd/types/device_addr.hpp>
#include <pybind11/operators.h>
#include <pybind11/stl.h>
#include <memory>
#include <string>


using namespace uhd::rfnoc;

namespace { // anon

using timekeeper = mb_controller::timekeeper;

// Make a "trampoline" class to help Pybind11
class PyTimekeeper : public timekeeper
{
public:
    /* Inherit the constructors */
    using timekeeper::timekeeper;

    /* Trampoline (need one for each virtual function) */
    uint64_t get_ticks_now(void) override
    {
        PYBIND11_OVERLOAD_PURE(uint64_t, /* Return type */
            timekeeper, /* Parent class */
            get_ticks_now /* Name of function in C++ (must match Python name) */
            /* (No) Argument(s) */
        );
    }
    uint64_t get_ticks_last_pps(void) override
    {
        PYBIND11_OVERLOAD_PURE(uint64_t, timekeeper, get_ticks_last_pps);
    }
    void set_ticks_now(const uint64_t ticks) override
    {
        PYBIND11_OVERLOAD_PURE(void, timekeeper, set_ticks_now, ticks);
    }
    void set_ticks_next_pps(const uint64_t ticks) override
    {
        PYBIND11_OVERLOAD_PURE(void, timekeeper, set_ticks_next_pps, ticks);
    }
};

} // namespace


void export_rfnoc(py::module& m)
{
    py::class_<block_id_t>(m, "block_id")
        // Constructors
        .def(py::init<>())
        .def(py::init<std::string>())
        .def(py::init<size_t, std::string&, size_t>(),
            py::arg("device_no"),
            py::arg("block_name"),
            py::arg("block_ctr") = 0)

        // Methods
        .def("__str__", &block_id_t::to_string)
        .def("to_string", &block_id_t::to_string)
        .def("is_valid_blockname", &block_id_t::is_valid_blockname)
        .def("is_valid_block_id", &block_id_t::is_valid_block_id)
        .def("match", &block_id_t::match)
        .def("get", &block_id_t::get)
        .def("get_local", &block_id_t::get_local)
        .def("get_tree_root", &block_id_t::get_tree_root)
        .def("get_device_no", &block_id_t::get_device_no)
        .def("get_block_count", &block_id_t::get_block_count)
        .def("get_block_name", &block_id_t::get_block_name)
        .def("set", py::overload_cast<const std::string&>(&block_id_t::set))
        .def("set",
            py::overload_cast<const size_t, const std::string&, const size_t>(
                &block_id_t::set),
            py::arg("device_no"),
            py::arg("block_name"),
            py::arg("block_ctr") = 0)
        .def("set_device_no", &block_id_t::set_device_no)
        .def("set_block_name", &block_id_t::set_block_name)
        .def("set_block_count", &block_id_t::set_block_count)

        // Operators
        .def(py::self == py::self)
        .def(py::self != py::self)
        .def(py::self < py::self)
        .def(py::self > py::self)
        .def(py::self == std::string());
    // This will allow functions in Python that take a block_id to also take
    // a string:
    py::implicitly_convertible<std::string, block_id_t>();

    py::enum_<graph_edge_t::edge_t>(m, "edge")
        .value("static", graph_edge_t::STATIC)
        .value("dynamic", graph_edge_t::DYNAMIC)
        .value("rx_stream", graph_edge_t::RX_STREAM)
        .value("tx_stream", graph_edge_t::TX_STREAM)
        .export_values();

    py::class_<graph_edge_t>(m, "graph_edge")
        // Constructors
        .def(py::init<>())
        .def(py::init<const size_t,
            const size_t,
            const graph_edge_t::edge_t,
            const bool>())

        // Properties
        .def_readwrite("src_blockid", &graph_edge_t::src_blockid)
        .def_readwrite("src_port", &graph_edge_t::src_port)
        .def_readwrite("dst_blockid", &graph_edge_t::dst_blockid)
        .def_readwrite("dst_port", &graph_edge_t::dst_port)
        .def_readwrite("edge", &graph_edge_t::edge)
        .def_readwrite(
            "property_propagation_active", &graph_edge_t::property_propagation_active)

        // Methods
        .def("__str__", &graph_edge_t::to_string)
        .def("to_string", &graph_edge_t::to_string);

    py::class_<rfnoc_graph, rfnoc_graph::sptr>(m, "rfnoc_graph")
        .def(py::init(&rfnoc_graph::make))

        // General RFNoC Graph methods
        // TODO: Templated methods??
        .def("find_blocks",
            [](rfnoc_graph::sptr& self, const std::string& block_id_hint) {
                return self->find_blocks(block_id_hint);
            })
        .def("has_block",
            [](rfnoc_graph::sptr& self, const block_id_t& block_id) {
                return self->has_block(block_id);
            })
        .def("get_block",
            [](rfnoc_graph::sptr& self, const block_id_t& block_id) {
                return self->get_block(block_id);
            })
        .def("is_connectable", &rfnoc_graph::is_connectable)
        .def("connect",
            py::overload_cast<const block_id_t&, size_t, const block_id_t&, size_t, bool>(
                &rfnoc_graph::connect))
        .def("connect",
            py::overload_cast<uhd::tx_streamer::sptr,
                size_t,
                const block_id_t&,
                size_t,
                uhd::transport::adapter_id_t>(&rfnoc_graph::connect),
            py::arg("streamer"),
            py::arg("strm_port"),
            py::arg("dst_blk"),
            py::arg("dst_blk"),
            py::arg("adapter_id") = uhd::transport::NULL_ADAPTER_ID)
        .def("connect",
            py::overload_cast<const block_id_t&,
                size_t,
                uhd::rx_streamer::sptr,
                size_t,
                uhd::transport::adapter_id_t>(&rfnoc_graph::connect),
            py::arg("src_blk"),
            py::arg("src_blk"),
            py::arg("streamer"),
            py::arg("strm_port"),
            py::arg("adapter_id") = uhd::transport::NULL_ADAPTER_ID)
        .def("enumerate_adapters_from_src", &rfnoc_graph::enumerate_adapters_from_src)
        .def("enumerate_adapters_to_dst", &rfnoc_graph::enumerate_adapters_to_dst)
        .def("enumerate_static_connections", &rfnoc_graph::enumerate_static_connections)
        .def("enumerate_active_connections", &rfnoc_graph::enumerate_active_connections)
        .def("commit", &rfnoc_graph::commit)
        .def("release", &rfnoc_graph::release)
        .def("create_rx_streamer", &rfnoc_graph::create_rx_streamer)
        .def("create_tx_streamer", &rfnoc_graph::create_tx_streamer)
        .def("get_num_mboards", &rfnoc_graph::get_num_mboards)
        .def(
            "get_mb_controller", &rfnoc_graph::get_mb_controller, py::arg("mb_index") = 0)
        .def("synchronize_devices", &rfnoc_graph::synchronize_devices)
        .def("get_tree", &rfnoc_graph::get_tree);

    py::class_<mb_controller, mb_controller::sptr>(m, "mb_controller")
        .def("get_num_timekeepers", &mb_controller::get_num_timekeepers)
        .def("get_timekeeper", &mb_controller::get_timekeeper)
        .def("init", &mb_controller::init)
        .def("get_mboard_name", &mb_controller::get_mboard_name)
        .def("set_time_source", &mb_controller::set_time_source)
        .def("get_time_source", &mb_controller::get_time_source)
        .def("get_time_sources", &mb_controller::get_time_sources)
        .def("set_clock_source", &mb_controller::set_clock_source)
        .def("get_clock_source", &mb_controller::get_clock_source)
        .def("get_clock_sources", &mb_controller::get_clock_sources)
        .def("set_sync_source",
            py::overload_cast<const std::string&, const std::string&>(
                &mb_controller::set_sync_source))
        .def("set_sync_source",
            py::overload_cast<const uhd::device_addr_t&>(&mb_controller::set_sync_source))
        .def("get_sync_source", &mb_controller::get_sync_source)
        .def("get_sync_sources", &mb_controller::get_sync_sources)
        .def("set_clock_source_out", &mb_controller::set_clock_source_out)
        .def("set_time_source_out", &mb_controller::set_time_source_out)
        .def("get_sensor", &mb_controller::get_sensor)
        .def("get_sensor_names", &mb_controller::get_sensor_names)
        .def("get_eeprom", &mb_controller::get_eeprom)
        .def("synchronize", &mb_controller::synchronize)
        .def("get_gpio_banks", &mb_controller::get_gpio_banks)
        .def("get_gpio_srcs", &mb_controller::get_gpio_srcs)
        .def("get_gpio_src", &mb_controller::get_gpio_src)
        .def("set_gpio_src", &mb_controller::set_gpio_src);

    py::class_<timekeeper, PyTimekeeper, timekeeper::sptr>(m, "timekeeper")
        // Methods
        // FIXME? .def(py::init<>())
        .def("get_time_now", &timekeeper::get_time_now)
        .def("get_ticks_now", &timekeeper::get_ticks_now)
        .def("get_time_last_pps", &timekeeper::get_time_last_pps)
        .def("get_ticks_last_pps", &timekeeper::get_ticks_last_pps)
        .def("set_time_now", &timekeeper::set_time_now)
        .def("set_ticks_now", &timekeeper::set_ticks_now)
        .def("set_time_next_pps", &timekeeper::set_time_next_pps)
        .def("set_ticks_next_pps", &timekeeper::set_ticks_next_pps)
        .def("get_tick_rate", &timekeeper::get_tick_rate);

    py::class_<noc_block_base, noc_block_base::sptr>(m, "noc_block_base")
        .def("get_unique_id", &noc_block_base::get_unique_id)
        .def("get_num_input_ports", &noc_block_base::get_num_input_ports)
        .def("get_num_output_ports", &noc_block_base::get_num_output_ports)
        .def("get_noc_id", &noc_block_base::get_noc_id)
        .def("get_block_id", &noc_block_base::get_block_id)
        .def("get_tick_rate", &noc_block_base::get_tick_rate)
        .def("get_mtu", &noc_block_base::get_mtu)
        .def("get_block_args", &noc_block_base::get_block_args)
        .def("get_tree", [](noc_block_base::sptr& self) {
            // Force the non-const `get_tree`
            uhd::property_tree::sptr tree = self->get_tree();
            return tree;
        });
}

#endif /* INCLUDED_UHD_RFNOC_PYTHON_HPP */
