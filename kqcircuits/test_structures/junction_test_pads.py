# Copyright (c) 2019-2021 IQM Finland Oy.
#
# All rights reserved. Confidential and proprietary.
#
# Distribution or reproduction of any information contained herein is prohibited without IQM Finland Oy’s prior
# written permission.

import numpy

from kqcircuits.defaults import default_squid_type
from kqcircuits.elements.qubits.qubit import Qubit
from kqcircuits.pya_resolver import pya
from kqcircuits.util.parameters import Param, pdt
from kqcircuits.util.library_helper import load_libraries, to_library_name
from kqcircuits.elements.element import Element
from kqcircuits.squids import squid_type_choices
from kqcircuits.test_structures.test_structure import TestStructure
from kqcircuits.defaults import default_junction_test_pads_type


class JunctionTestPads(TestStructure):
    """Base class for junction test structures."""

    pad_width = Param(pdt.TypeDouble, "Pad width", 500, unit="μm")
    area_height = Param(pdt.TypeDouble, "Area height", 1900, unit="μm")
    area_width = Param(pdt.TypeDouble, "Area width", 1300, unit="μm")
    squid_type = Param(pdt.TypeString, "SQUID Type", default_squid_type, choices=squid_type_choices)
    junctions_horizontal = Param(pdt.TypeBoolean, "Horizontal (True) or vertical (False) junctions", True)
    pad_spacing = Param(pdt.TypeDouble, "Spacing between different pad pairs", 100, unit="μm")
    only_pads = Param(pdt.TypeBoolean, "Only produce pads, no junctions", False)
    pad_configuration = Param(pdt.TypeString, "Pad configuration", "2-port",
                              choices=[["2-port", "2-port"], ["4-port", "4-port"]])
    junction_width = Param(pdt.TypeDouble, "Junction width for code generated squids", 0.02,
                           docstring="Junction width (only used for code generated squids)")

    produce_squid = Qubit.produce_squid

    @classmethod
    def create(cls, layout, junction_test_type=None, **parameters):
        """Create a JunctionTestPads cell in layout.

        If junction_test_type is unknown the default is returned.

        Overrides Element.create(), so that functions like add_element() and insert_cell() will call this instead.

        Args:
            layout: pya.Layout object where this cell is created
            junction_test_type (str): name of the JunctionTestPads subclass
            **parameters: PCell parameters for the element as keyword arguments

        Returns:
            the created JunctionTestPads cell
        """

        if junction_test_type is None:
            junction_test_type = to_library_name(cls.__name__)

        library_layout = (load_libraries(path=cls.LIBRARY_PATH)[cls.LIBRARY_NAME]).layout()
        if junction_test_type in library_layout.pcell_names():   #code generated
            pcell_class = type(library_layout.pcell_declaration(junction_test_type))
            return Element._create_cell(pcell_class, layout, **parameters)
        elif library_layout.cell(junction_test_type):    # manually designed
            return layout.create_cell(junction_test_type, cls.LIBRARY_NAME)
        else:   # fallback is the default
            return JunctionTestPads.create(layout, junction_test_type=default_junction_test_pads_type, **parameters)

    def _produce_impl(self):

        if self.pad_configuration == "2-port":
            self._produce_two_port_junction_tests()
        if self.pad_configuration == "4-port":
            self._produce_four_port_junction_tests()

        super().produce_impl()

    def _produce_two_port_junction_tests(self):

        pads_region = pya.Region()
        pad_step = self.pad_spacing + self.pad_width
        arm_width = 8

        junction_idx = 0
        if self.junctions_horizontal:
            for x in numpy.arange(self.pad_spacing*1.5 + self.pad_width, self.area_width - pad_step, 2*pad_step,
                                  dtype=numpy.double):
                for y in numpy.arange(self.pad_spacing + self.pad_width*0.5, self.area_height - self.pad_width / 2,
                                      pad_step, dtype=numpy.double):
                    self.produce_pad(x - pad_step / 2, y, pads_region, self.pad_width, self.pad_width)
                    self.produce_pad(x + pad_step / 2, y, pads_region, self.pad_width, self.pad_width)
                    self._produce_junctions(x, y, pads_region, arm_width)
                    self.refpoints["probe_{}_l".format(junction_idx)] = pya.DPoint(x - pad_step / 2, y)
                    self.refpoints["probe_{}_r".format(junction_idx)] = pya.DPoint(x + pad_step / 2, y)
                    junction_idx += 1
        else:
            for y in numpy.arange(self.pad_spacing*1.5 + self.pad_width, self.area_height - pad_step, 2*pad_step,
                                  dtype=numpy.double):
                for x in numpy.arange(self.pad_spacing + self.pad_width*0.5, self.area_width - self.pad_width / 2,
                                      pad_step, dtype=numpy.double):
                    self.produce_pad(x, y - pad_step / 2, pads_region, self.pad_width, self.pad_width)
                    self.produce_pad(x, y + pad_step / 2, pads_region, self.pad_width, self.pad_width)
                    self._produce_junctions(x, y, pads_region, arm_width)
                    self.refpoints["probe_{}_l".format(junction_idx)] = pya.DPoint(x, y - pad_step / 2)
                    self.refpoints["probe_{}_r".format(junction_idx)] = pya.DPoint(x, y + pad_step / 2)
                    junction_idx += 1

        self.produce_etched_region(pads_region, pya.DPoint(self.area_width / 2, self.area_height / 2), self.area_width,
                                   self.area_height)

    def _produce_junctions(self, x, y, pads_region, arm_width):

        if not self.only_pads:
            self._produce_squid_and_arms(x, y, pads_region, arm_width)

    def _produce_four_port_junction_tests(self):

        pads_region = pya.Region()
        junction_idx = 0
        step = 2 * (self.pad_width + self.pad_spacing)

        for x in numpy.arange(self.pad_spacing*1.5 + self.pad_width, self.area_width - step / 2, step,
                              dtype=numpy.double):
            for y in numpy.arange(self.pad_spacing*1.5 + self.pad_width, self.area_height - step / 2, step,
                                  dtype=numpy.double):

                if self.only_pads:
                    self.produce_four_point_pads(pads_region, self.pad_width, self.pad_width, self.pad_spacing,
                                                 self.pad_spacing, False, pya.DTrans(0, False, x, y),
                                                 "probe_{}".format(junction_idx))
                else:
                    self.produce_four_point_pads(pads_region, self.pad_width, self.pad_width, self.pad_spacing,
                                                 self.pad_spacing, True,
                                                 pya.DTrans(0 if self.junctions_horizontal else 1, False, x, y),
                                                 "probe_{}".format(junction_idx))
                    self._produce_junctions(x, y, pads_region, 5)

                junction_idx += 1

        self.produce_etched_region(pads_region, pya.DPoint(self.area_width / 2, self.area_height / 2), self.area_width,
                                   self.area_height)

    def _produce_squid_and_arms(self, x, y, pads_region, arm_width):
        """Produces a squid and arms for connecting it to pads.

        The squid is inserted as a subcell. The arm shapes are inserted to pads_region, and their shape depends on
        arm_width and self.junctions_horizontal.

        Args:
           x: x-coordinate of squid origin
           y: y-coordinate of squid origin
           pads_region: Region to which the arm shapes are inserted
           arm_width: width of the arms

        """

        extra_arm_length = self.extra_arm_length
        junction_spacing = self.junction_spacing

        if self.junctions_horizontal:
            # squid
            trans = pya.DCplxTrans(x, y - junction_spacing)
            region_unetch, squid_ref_rel = self.produce_squid(trans)
            pos_rel_squid_top = squid_ref_rel["port_common"]
            pads_region.insert(region_unetch)
            # arm below
            arm1 = pya.DBox(
                pya.DPoint(x + 11 + extra_arm_length, y - junction_spacing),
                pya.DPoint(x - self.pad_spacing / 2, y - arm_width - junction_spacing),
            )
            pads_region.insert(arm1.to_itype(self.layout.dbu))
            # arm above
            arm2 = pya.DBox(
                trans*pos_rel_squid_top + pya.DVector(-4, 0),
                trans*pos_rel_squid_top + pya.DVector(self.pad_spacing / 2, arm_width),
            )
            pads_region.insert(arm2.to_itype(self.layout.dbu))
        else:
            # squid
            trans = pya.DCplxTrans(x - junction_spacing, y)
            region_unetch, squid_ref_rel = self.produce_squid(trans)
            pos_rel_squid_top = squid_ref_rel["port_common"]
            pads_region.insert(region_unetch)
            # arm below
            arm1 = pya.DBox(
                pya.DPoint(x + 11 + extra_arm_length - junction_spacing, y),
                pya.DPoint(x - 11 - extra_arm_length - junction_spacing, y - arm_width),
            )
            pads_region.insert(arm1.to_itype(self.layout.dbu))
            arm2 = pya.DBox(
                pya.DPoint(x + arm_width / 2 - junction_spacing, y),
                pya.DPoint(x - arm_width / 2 - junction_spacing, y - self.pad_spacing / 2),
            )
            pads_region.insert(arm2.to_itype(self.layout.dbu))
            # arm above
            arm3 = pya.DBox(
                trans*pos_rel_squid_top + pya.DVector(-arm_width / 2, 0),
                trans*pos_rel_squid_top + pya.DVector(arm_width / 2, self.pad_spacing / 2),
            )
            pads_region.insert(arm3.to_itype(self.layout.dbu))
