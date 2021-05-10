# Copyright (c) 2019-2021 IQM Finland Oy.
#
# All rights reserved. Confidential and proprietary.
#
# Distribution or reproduction of any information contained herein is prohibited without IQM Finland Oy’s prior
# written permission.
from kqcircuits.simulations.xmons_direct_coupling_sim import XMonsDirectCouplingSim


def test_ansys_export_produces_output_files(layout, perform_test_ansys_export_produces_output_files):
    perform_test_ansys_export_produces_output_files(XMonsDirectCouplingSim(layout))


def test_sonnet_export_produces_output_files(layout, perform_test_sonnet_export_produces_output_files):
    perform_test_sonnet_export_produces_output_files(XMonsDirectCouplingSim(layout))
