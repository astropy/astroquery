#!/usr/bin/env python
# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

from abc import abstractmethod, ABC
from enum import Enum


class PropertyConstraint(object):
    def __init__(self, expr):
        if not isinstance(expr, PropertiesExpr) and not isinstance(expr, str):
            raise TypeError('`expr` is not of type str nor PropertiesExpr')

        self.expr = expr
        self.request_payload = dict()
        self._compute_payload()

    def _compute_payload(self):
        if isinstance(self.expr, str):
            self.request_payload['expr'] = self.expr
            return

        self.request_payload['expr'] = self.expr.eval()

    def __repr__(self):
        result = "Properties constraints' request payload :\n{0}".format(self.request_payload)
        return result


class OperandExpr(Enum):
    Inter = 1,
    Union = 2,
    Subtr = 3


class PropertiesExpr(ABC):
    @abstractmethod
    def eval(self):
        pass


class ChildNode(PropertiesExpr):
    def __init__(self, condition):
        assert condition is not None
        self.condition = condition

    def eval(self):
        return str(self.condition)


class ParentNode(PropertiesExpr):
    def __init__(self, operand, left_expr, right_expr):
        assert isinstance(right_expr, PropertiesExpr), TypeError('`right_expr` is not of type PropertiesExpr')
        assert isinstance(left_expr, PropertiesExpr), TypeError('`left_expr` is not of type PropertiesExpr')

        if operand not in (OperandExpr.Inter, OperandExpr.Union, OperandExpr.Subtr):
            raise TypeError('`operand` is not of type OperandExpr')

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
