from pathlib import Path
from time import strftime
from typing import Callable, List

import gym
import numpy as np
from gym import Env
from numpy import ndarray

from deepq import ValueFunctionApproximation, DeepQNetwork
from plot import plot_training_summary, plot_cartpole_value_function
from replay import Experience
from train import train, PeriodicTrainingCallback, TrainingSummary


def timestamp() -> str:
    return strftime('%Y%m%d-%H%M%S')


def save_cartpole_q_plot_callback(period: int = 10000,
                                  directory: Path = None,
                                  show_advantage=False):
    name = 'advantage' if show_advantage else 'value'

    if directory is None:
        directory = Path('data') / 'plots' / 'CartPole-v0' / name / timestamp()

    def save(summary: TrainingSummary):
        if directory is not None:
            directory.mkdir(exist_ok=True, parents=True)

        save_to_file = None if directory is None else \
            directory / f'{name}_step{summary.timestep}'

        plot_cartpole_value_function(summary.q, save_to_file=save_to_file, show_advantage=show_advantage)

    return PeriodicTrainingCallback(action=save, period=period)


def run(env: Env, policy: Callable[[ndarray], ndarray], render=True, episodes=50):
    episode_rewards: List[float] = []
    for _ in range(episodes):
        observation = env.reset()
        done = False
        episode_reward = 0
        while not done:
            if render:
                env.render()
            observation, reward, done, info = env.step(policy(observation))
            episode_reward += reward
        print(f'Episode reward: {episode_reward}')
        episode_rewards.append(episode_reward)

    return episode_rewards


def run_greedy(q: ValueFunctionApproximation, render=True):
    run(q.env, lambda observation: q.greedy_action(observation), render=render)


class ZeroQ(ValueFunctionApproximation):
    def __init__(self, env: Env):
        super().__init__(env)

    def all_action_values_for(self, observations: ndarray):
        return np.zeros((observations.shape[0], self.env.action_space.n))

    def update(self, experiences: List[Experience]):
        pass


def train_and_plot(env_name,
                   extra_callbacks: List[PeriodicTrainingCallback] = list(),
                   run_name=timestamp(),
                   is_solved: Callable[[TrainingSummary], bool] = lambda s: False):
    env = gym.make(env_name)

    summary = train(DeepQNetwork(env),
                    callbacks=[PeriodicTrainingCallback.save_dqn(
                        directory=Path('data') / 'models' / env_name / run_name)] + extra_callbacks,
                    is_solved=is_solved)
    plot_training_summary(summary, Path('data') / 'plots' / env_name / 'summary' / f'summary{run_name}')


def average_return_above(minimum_average_return: float, num_last_episodes: int = 100):
    def is_stable(summary: TrainingSummary):
        return len(summary.returns) >= num_last_episodes and \
               np.average(summary.returns[-num_last_episodes:]) >= minimum_average_return

    return is_stable


def train_cartpole():
    train_and_plot('CartPole-v0', extra_callbacks=[
        save_cartpole_q_plot_callback(),
        save_cartpole_q_plot_callback(show_advantage=True)],
                   is_solved=average_return_above(195))


def train_lunar_lander():
    train_and_plot('LunarLander-v2', is_solved=average_return_above(200),
                   extra_callbacks=[PeriodicTrainingCallback.render()])


def train_mountain_car():
    train_and_plot('MountainCar-v0', is_solved=average_return_above(-110),
                   extra_callbacks=[PeriodicTrainingCallback.render()])


if __name__ == '__main__':
    train_cartpole()
