#
# Copyright 2017 Ettus Research, National Instruments Company
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

set(USRP_MPM_FILES ${USRP_MPM_FILES})
set(USRP_MPM_XPORT_FILES
    ${CMAKE_CURRENT_SOURCE_DIR}/__init__.py
    ${CMAKE_CURRENT_SOURCE_DIR}/xportmgr_udp.py
)
list(APPEND USRP_MPM_FILES ${USRP_MPM_XPORT_FILES})
set(USRP_MPM_FILES ${USRP_MPM_FILES} PARENT_SCOPE)

