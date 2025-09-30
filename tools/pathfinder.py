from collections import deque
import heapq
from typing import List, Tuple, Optional


class Node:
    """A node class for A* pathfinding with f, g, h values."""

    def __init__(self, position: Tuple[int, int], g: float = 0, h: float = 0):
        self.position = position
        self.g = g  # Cost from start to this node
        self.h = h  # Heuristic cost from this node to goal
        self.f = g + h  # Total cost

    def __lt__(self, other):
        return self.f < other.f


class Pathfinder:
    def __init__(self, grid: List[List[int]]):
        """
        Initialize the Pathfinder with a 2D grid.

        Args:
            grid: 2D list representing the grid where 0 is passable, 1 is obstacle
        """
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0]) if self.rows > 0 else 0

    def get_neighbors(self, node: Tuple[int, int]) -> List[Tuple[Tuple[int, int], str, int]]:
        """
        Returns list of valid neighboring nodes with their movement cost.

        Args:
            node: Tuple (x, y) representing current position

        Returns:
            List of tuples containing (position, direction, cost)
        """
        x, y = node
        neighbors = []
        directions = [('UP', (x-1, y)), ('DOWN', (x+1, y)),
                     ('LEFT', (x, y-1)), ('RIGHT', (x, y+1))]

        for direction, (nx, ny) in directions:
            if 0 <= nx < self.rows and 0 <= ny < self.cols and self.grid[nx][ny] != 1:
                # Use terrain cost if available, otherwise default to 1
                cost = self.grid[nx][ny] if isinstance(self.grid[nx][ny], (int, float)) else 1
                neighbors.append(((nx, ny), direction, cost))
        return neighbors

    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> int:
        """
        Calculate Manhattan distance heuristic.

        Args:
            a: First coordinate tuple (x, y)
            b: Second coordinate tuple (x, y)

        Returns:
            Manhattan distance between points
        """
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def astar(self, start: Tuple[int, int], goal: Tuple[int, int]) -> Optional[List[str]]:
        """
        Find optimal path using A* algorithm.

        This implementation uses a priority queue to explore nodes with the lowest
        estimated total cost first. The algorithm combines Dijkstra's greed with
        BFS's shape to provide optimal paths with good performance.

        Args:
            start: Tuple (x, y) of start coordinates
            goal: Tuple (x, y) of goal coordinates

        Returns:
            List of direction strings representing the optimal path, or None if no path found

        Examples:
            >>> grid = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
            >>> pathfinder = Pathfinder(grid)
            >>> path = pathfinder.astar((0, 0), (2, 2))
            >>> print(path)  # ['DOWN', 'DOWN', 'RIGHT'] or similar optimal path

        Notes:
            - Uses Manhattan distance as heuristic for 4-directional movement
            - Supports variable terrain costs beyond binary 0/1 system
            - Maintains compatibility with existing grid format and memory system
            - Provides optimal paths with efficient exploration order
        """
        # Edge case: Start and goal are the same
        if start == goal:
            return []

        # Edge case: Invalid start or goal coordinates
        if not self._is_valid_position(start) or not self._is_valid_position(goal):
            return None

        # Edge case: Start position is blocked
        if self.grid[start[0]][start[1]] == 1:
            return None

        frontier = []
        start_node = Node(start, g=0, h=self._heuristic(start, goal))
        heapq.heappush(frontier, (start_node.f, start_node))

        came_from = {start: None}
        cost_so_far = {start: 0}

        while frontier:
            current_f, current_node = heapq.heappop(frontier)
            current = current_node.position

            # Goal reached
            if current == goal:
                return self._reconstruct_path(came_from, current)

            # Explore neighbors
            for neighbor, direction, cost in self.get_neighbors(current):
                new_cost = cost_so_far[current] + cost

                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    priority = new_cost + self._heuristic(neighbor, goal)
                    neighbor_node = Node(neighbor, g=new_cost, h=self._heuristic(neighbor, goal))

                    heapq.heappush(frontier, (priority, neighbor_node))
                    came_from[neighbor] = (current, direction)

        return None  # No path found

    def _is_valid_position(self, position: Tuple[int, int]) -> bool:
        """
        Check if a position is within grid bounds.

        Args:
            position: Tuple (x, y) to validate

        Returns:
            True if position is valid, False otherwise
        """
        x, y = position
        return 0 <= x < self.rows and 0 <= y < self.cols

    def _reconstruct_path(self, came_from: dict, current: Tuple[int, int]) -> List[str]:
        """
        Reconstruct the path from start to goal using the came_from dictionary.

        Args:
            came_from: Dictionary mapping positions to (parent_position, direction) tuples
            current: Current position (goal position)

        Returns:
            List of direction strings representing the path
        """
        path = []
        while current is not None:
            current, direction = came_from[current]
            if direction is not None:
                path.append(direction)

        path.reverse()
        return path

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