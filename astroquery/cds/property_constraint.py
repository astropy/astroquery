#!/usr/bin/env python
# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

from abc import abstractmethod, ABC
from enum import Enum


class PropertyConstraint(object):
    """
    PropertyConstraint's class definition

    The user can specify a constraint acting only
    on properties too. The MOCServer asks for an
    algebraic expression dealing with properties.
    Example : a user can ask the MOCServer all datasets
    having the word CDS(Center of astronomical Data of
    Strasbourg) in its ID property or/and a moc_sky_fraction
    < 1 %

    """

    def __init__(self, expression):
        """
        PropertyConstraint's constructor

        :param expression:
            can be a PropertiesExpr or a string
        """

        if not isinstance(expression, PropertiesExpr) and not isinstance(expression, str):
            raise TypeError

        self.expr = expression
        self.request_payload = dict()
        self.compute_payload()

    def compute_payload(self):
        """Update the property constraints payload"""
        if isinstance(self.expr, str):
            self.request_payload = {'expr': self.expr}
        else:
            self.request_payload = {'expr': self.expr.eval()}

    def __repr__(self):
        result = "Properties constraints' request payload :\n{0}".format(self.request_payload)
        return result


class OperandExpr(Enum):
    """Operand Enum which allow the user to define relationship between expr"""
    Inter = 1,
    Union = 2,
    Subtr = 3


class PropertiesExpr(ABC):
    """
    General expression interface

    Expressions are built like a binary tree. A parent expression can
    have one or two children. The parent defines an operand between
    its two children (if it is a ParentNode) or nothing in
    the other case (only one child).

    """

    @abstractmethod
    def eval(self):
        """
        Evaluate recursively the whole expression

        Returns a str understandable by the MOCServer
        """

        pass


class ChildNode(PropertiesExpr):
    """Leaf expression node of the binary tree expression"""

    def __init__(self, condition):
        assert condition is not None
        self.condition = condition

    def eval(self):
        return str(self.condition)


class ParentNode(PropertiesExpr):
    """Parent expression node of the binary tree expression"""

    def __init__(self, operand, left_expr, right_expr):
        if not isinstance(right_expr, PropertiesExpr) or not isinstance(left_expr, PropertiesExpr):
            raise TypeError

        if operand not in (OperandExpr.Inter, OperandExpr.Union, OperandExpr.Subtr):
            raise TypeError

        self.left_expr = left_expr
        self.right_expr = right_expr
        self.operand = operand

    def eval(self):
        left_expr_str = str(self.left_expr.eval())
        right_expr_str = str(self.right_expr.eval())

        operand_str = " &! "
        if self.operand is OperandExpr.Inter:
            operand_str = " && "
        elif self.operand is OperandExpr.Union:
            operand_str = " || "

        if isinstance(self.left_expr, ParentNode):
            left_expr_str = '(' + left_expr_str + ')'
        if isinstance(self.right_expr, ParentNode):
            right_expr_str = '(' + right_expr_str + ')'

        return left_expr_str + operand_str + right_expr_str
