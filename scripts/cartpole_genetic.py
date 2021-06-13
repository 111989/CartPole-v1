"""
    Genetic Algorithm/ Neural Network 
    Implementation for balancing 
    CartPole-v1 from OpenAI Gym"""

import gym
import argparse
import numpy as np
from bisect import bisect_right
import matplotlib.pyplot as plt

class MyEnvironment:
    def __init__(self, environment_name: str, action = None, observation = None) -> None:
        self.environment_name = environment_name
        self.environment = gym.make(self.environment_name)
        self.action = action
        self.observation = observation
        if 'CartPole' in self.environment_name:
            self.n_bins = 20
            self.bins = [np.linspace(-4.8, 4.8, self.n_bins), \
                np.linspace(-4, 4, self.n_bins), \
                    np.linspace(-0.418, 0.418, self.n_bins), \
                        np.linspace(-4, 4, self.n_bins)]

    def get_environment_name(self) -> str: 
        """Returns the name of the environment"""
        return self.environment.unwrapped.spec.id 

    def get_action_space(self):
        return self.environment.action_space

    def get_action_space_length(self):
        if 'CartPole' in self.environment_name:
            return 2
        return self.environment.action_space.n

    def get_observation_space(self):
        return self.environment.observation_space
    
    def get_observation_space_length(self):
        if 'CartPole' in self.environment_name:
            return [self.n_bins+1] \
                * len(self.environment.observation_space.high)
        return [self.environment.horizon + 1]

    def set_observation(self, observation) -> None:
        self.observation = observation
        if 'CartPole' in self.environment_name:
            # discretize the observation
            observation_index = []
            for i in range(len(self.get_observation_space().high)):
                observation_index.append(np.digitize(self.observation[i], \
                    self.bins[i]) - 1)  # subtract 1 to convert bin into index 
            self.observation = tuple(observation_index)

    def display_environment(self):
        plt.imshow(self.environment.render(mode = 'rgb_array'))

    def reset(self):
        return self.environment.reset()

    def step(self):
        return self.environment.step(self.action)

    def render(self):
        return self.environment.render()

    def close(self):
        self.environment.close()



class Agent:
    """NN Agent"""
    def __init__(self, observation_space: int, action_space_length: int) -> None:
        self.observation_space = observation_space
        self.action_space_length = action_space_length
        self.weights = np.random.uniform(low = -1, high = 1, size = (self.observation_space, self.action_space_length))
        self.biases = np.random.uniform(low = -1, high = 1, size = (self.action_space_length))
        # Agent's fitness
        self.fitness = 0

    def act(self, observation: int) -> int: 
        """
            Returns Agent's action based on input 
            observation"""

        def sigmoid(x):
            """Activation function of neurons"""
            return 1.0 / (1.0 + np.exp(-x))

        a = np.matmul(observation, self.weights) + self.biases
        x = np.reshape(a = a, newshape = (self.action_space_length))
        return np.argmax(sigmoid(x))



class Population:
    def __init__(self, observation_space: int, action_space_length: int, population_count: int, mutation_rate: float) -> None:
        self.observation_space = observation_space
        self.action_space_length = action_space_length
        self.agents = [Agent(self.observation_space, self.action_space_length) \
            for _ in range(population_count)]
        self.mutation_rate = mutation_rate

    def get_cumulative_fitness(self) -> list:
        cumulative_fitness = [0]
        for i in range(len(self.agents)):
            cumulative_fitness.append(cumulative_fitness[-1] + self.agents[i].fitness)
        return cumulative_fitness

    def get_parents(self, cumulative_fitness: list):
        random1 = np.random.uniform(low = 0, high = cumulative_fitness[-1])
        random2 = np.random.uniform(low = 0, high = cumulative_fitness[-1])
        parent1 = self.agents[bisect_right(a = cumulative_fitness, x = random1)-1]
        parent2 = self.agents[bisect_right(a = cumulative_fitness, x = random2)-1]
        return parent1, parent2

    def get_successor(self):
        return Agent(self.observation_space, self.action_space_length)

    def mutate_successor(self, parent1, parent2, successor):
        def mutate_weights(parent1, parent2, successor, mutation_rate):
            for i in range(len(successor.weights)):
                for j in range(len(successor.weights[i])):
                    if np.random.random() > mutation_rate:
                        # mutate weights
                        successor.weights[i][j] = \
                            (parent1.weights[i][j] + parent2.weights[i][j]) / 2.0
                    else:
                        successor.weights[i][j] = np.random.uniform(-1, 1)

        def mutate_biases(parent1, parent2, successor, mutation_rate):
            for i in range(len(successor.biases)):
                if np.random.random() > mutation_rate:
                    # mutate biases
                    successor.biases[i] = \
                        (parent1.biases[i] + parent2.biases[i]) / 2.0
                else:
                    successor.biases[i] = np.random.uniform(-1, 1)
        
        mutate_weights(parent1, parent2, successor, self.mutation_rate)
        mutate_biases(parent1, parent2, successor, self.mutation_rate)
        return successor



def run_episode(environment, agent, episode_length: int, render_gym = False) -> float:
    observation = environment.reset()
    for _ in range(episode_length):
        if render_gym and 'CartPole' in environment.environment_name:
            environment.render()
        action = agent.act(observation)
        environment.action = action
        observation, reward, done, _ = environment.step()
        agent.fitness += reward
        if done:
            break
    return agent.fitness



def generate_next_generation(population) -> None:
    """
        Generates the next generation of the 
        population by means of evolution, and
        sets them as the new agents"""

    next_generation = []
    cumulative_fitness = population.get_cumulative_fitness()
    while(len(next_generation) < population_count):
        parent1, parent2 = population.get_parents(cumulative_fitness)
        successor = population.mutate_successor(parent1, parent2, population.get_successor())
        next_generation.append(successor)
    # update agents
    population.agents = next_generation

    

def plot_statistics(running_accuracy: float) -> None:
    plt.plot(running_accuracy)
    plt.xlabel(xlabel = 'Generation')
    plt.ylabel(ylabel = 'Average Score (Timesteps)')
    plt.grid()
    plt.savefig(fname = 'cartpole_genetic.jpg')
    plt.show()
    print("...DONE!")



def main():
    
    # initialize gym environment
    environment = MyEnvironment('CartPole-v1')
    # get inputs for agents from the environment and generate agents
    observation_space = environment.get_observation_space().shape[0] # 4 
    action_space_length = environment.get_action_space().n # 2 (Left or Right)
    population = Population(observation_space, action_space_length, population_count, mutation_rate)
    
    running_accuracy = []
    render_gym = True
    for generation in range(generations):
        cumulative_reward = 0.0
        for agent in population.agents:
            agent.fitness = run_episode(environment, agent, episode_length, render_gym)
            # accumulate reward        
            cumulative_reward += agent.fitness

        # calculate average fitness of the generation and print performance statistics
        generation_fitness = cumulative_reward / population_count
        print("Generation: %4d | Average Fitness: %2.0f" % (generation + 1, generation_fitness))
        running_accuracy.append(generation_fitness)
        # generate the next generation and update agents  
        generate_next_generation(population)

    environment.close()
    # plot performance statistics
    plot_statistics(running_accuracy)


    
if __name__ == "__main__":
    
    # parse input arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--generations', type = int, default = 10, \
        help = 'Number of generations')
    parser.add_argument('--steps', type = int, default = 500, \
        help = 'Episode length')
    parser.add_argument('--population', type = int, default = 20, \
        help = 'Population count')
    parser.add_argument('--mutation', type = float, default = 0.01, \
        help = 'Mutation rate')
    
    args = vars(parser.parse_args())
    generations = int(args['generations'])
    episode_length = int(args['steps'])
    population_count = int(args['population'])
    mutation_rate = float(args['mutation'])

    main()
