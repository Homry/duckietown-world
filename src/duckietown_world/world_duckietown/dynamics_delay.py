import bisect

import math
from typing import Any, Tuple

import numpy as np

from duckietown_world.world_duckietown.types import TSE2v
from .platform_dynamics import PlatformDynamics, PlatformDynamicsFactory

__all__ = ["ApplyDelay", "DelayedDynamics"]


class ApplyDelay(PlatformDynamicsFactory):
    factory: PlatformDynamicsFactory

    def __init__(self, factory, delay: float, u0):
        self.factory = factory
        self.delay = delay
        self.u0 = u0

    def initialize(self, c0: TSE2v, t0: float = 0, seed: int = None) -> PlatformDynamics:
        """
        Returns the dynamics initalized at a certain configuration.

        :param c0: configuration in TSE2
        :param t0: time in which to sstart
        :param seed: seed for a possible random number generator

        """
        state0 = self.factory.initialize(c0, t0, seed)
        return DelayedDynamics(state0, self.delay, t0, self.u0)


class DelayedDynamics(PlatformDynamics):
    state: PlatformDynamics

    def __init__(self, state, delay, t0, u0, commands=None, timestamps=None):
        self.state = state
        self.commands = commands or []
        self.timestamps = timestamps or []
        self.t = t0
        self.delay = delay
        self.u0 = u0

        if self.timestamps:
            i, _, _ = self.get_commands_at(self.timestamps[-1] - self.delay)
            self.commands = self.commands[i:]
            self.timestamps = self.timestamps[i:]

    def get_commands_at(self, t) -> Tuple[int, float, Any]:
        if t < self.timestamps[0]:
            return 0, 0, self.u0

        # a = np.array(self.timestamps)
        a = self.timestamps
        idx = bisect.bisect_left(a, t)
        # idx2 = np.searchsorted(a, t, side="left")
        # assert idx==idx2, (idx, idx2)

        if idx > 0 and (idx == len(a) or math.fabs(t - a[idx - 1]) < math.fabs(t - a[idx])):
            return idx, a[idx], self.commands[idx - 1]
        else:
            return idx, a[idx], self.commands[idx]

    def integrate(self, dt: float, commands) -> "DelayedDynamics":
        """
        Returns the result of applying commands for dt.

        :param dt: time interval
        :param commands: class-specific commands
        :return: the next state
        """
        self.commands.append(commands)
        self.timestamps.append(self.t)
        self.t += dt

        i, told, use_commands = self.get_commands_at(self.t - self.delay)
        # print(f't = {self.t}, t old = {told}'  )
        state2 = self.state.integrate(dt, use_commands)

        next_state = DelayedDynamics(
            state2,
            self.delay,
            self.t,
            self.u0,
            commands=list(self.commands),
            timestamps=list(self.timestamps),
        )
        return next_state

    def TSE2_from_state(self) -> TSE2v:
        return self.state.TSE2_from_state()
