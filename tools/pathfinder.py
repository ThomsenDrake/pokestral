from collections import deque
import heapq

class Pathfinder:
    def __init__(self, grid):
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0]) if self.rows > 0 else 0

    def get_neighbors(self, node):
        """Returns list of valid neighboring nodes with their movement cost."""
        x, y = node
        neighbors = []
        directions = [('UP', (x-1, y)), ('DOWN', (x+1, y)),
                    ('LEFT', (x, y-1)), ('RIGHT', (x, y+1))]

        for direction, (nx, ny) in directions:
            if 0 <= nx < self.rows and 0 <= ny < self.cols and self.grid[nx][ny] != 1:
                neighbors.append(((nx, ny), direction, 1))  # (position, direction, cost)
        return neighbors

    def bfs(self, start, goal):
        """Breadth-First Search algorithm for pathfinding."""
        frontier = deque([(start, [])])
        came_from = {start: None}

        while frontier:
            current, path = frontier.popleft()

            if current == goal:
                return path

            for neighbor, direction, _ in self.get_neighbors(current):
                if neighbor not in came_from:
                    frontier.append((neighbor, path + [direction]))
                    came_from[neighbor] = current

        return None  # No path found

    def dijkstra(self, start, goal):
        """Dijkstra's algorithm for pathfinding with weighted edges."""
        frontier = []
        heapq.heappush(frontier, (0, start, []))
        came_from = {start: None}
        cost_so_far = {start: 0}

        while frontier:
            current_cost, current, path = heapq.heappop(frontier)

            if current == goal:
                return path

            for neighbor, direction, cost in self.get_neighbors(current):
                new_cost = cost_so_far[current] + cost
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    heapq.heappush(frontier, (new_cost, neighbor, path + [direction]))
                    came_from[neighbor] = current

        return None  # No path found