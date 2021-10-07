# -*- coding: utf-8 -*-
"""
Tests for greenlet.

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from gc import collect
from gc import get_objects

from greenlet import greenlet as RawGreenlet
from greenlet import getcurrent

class CleanupMixin(object):

    def wait_for_pending_cleanups(self):
        from time import sleep
        from time import time
        from greenlet._greenlet import get_pending_cleanup_count
        sleep_time = 0.001
        # Always sleep at least once to let other threads run
        sleep(sleep_time)
        quit_after = time() + 10
        while get_pending_cleanup_count():
            sleep(sleep_time)
            if time() > quit_after:
                break
        collect()

    def count_objects(self, kind=list, exact_kind=True):
        # pylint:disable=unidiomatic-typecheck
        # Collect the garbage.
        for _ in range(3):
            collect()
        if exact_kind:
            return sum(
                1
                for x in get_objects()
                if type(x) is kind
            )
        # instances
        return sum(
            1
            for x in get_objects()
            if isinstance(x, kind)
        )

    # TODO: Ensure we don't leak greenlets, everything gets GC'd.
    greenlets_before_test = 0
    expect_greenlet_leak = False

    def count_greenlets(self):
        """
        Find all the greenlets and subclasses tracked by the GC.
        """
        return self.count_objects(RawGreenlet, False)

    def setUp(self):
        # Ensure the main greenlet exists, otherwise the first test
        # gets a false positive leak
        getcurrent()
        self.wait_for_pending_cleanups()
        self.greenlets_before_test = self.count_greenlets()

    def tearDown(self):
        self.wait_for_pending_cleanups()
        greenlets_after_test = self.count_greenlets()
        if self.expect_greenlet_leak:
            if greenlets_after_test <= self.greenlets_before_test:
                # Turn this into self.fail for debugging
                print("WARNING:"
                    "Expected to leak greenlets but did not; expected more than %d but found %d"
                    % (self.greenlets_before_test, greenlets_after_test)
                )
        else:
            if greenlets_after_test > self.greenlets_before_test:
                self.fail(
                    "Leaked greenlets; expected no more than %d but found %d"
                    % (self.greenlets_before_test, greenlets_after_test)
                )

Cleanup = CleanupMixin
