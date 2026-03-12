class GridManager:
    def __init__(self, width: int, height: int, element_w: list[int], element_h: list[int]):
        self.gridW = element_w
        self.gridH = element_h
        self.rows = len(element_h)
        self.cols = len(element_w)
        if sum(self.gridH) + (self.rows - 1) > height:
            raise ValueError(f"Not enough height for the given number of rows: {sum(self.gridH) + (self.rows - 1)} > {height}")
        if sum(self.gridW) + (self.cols - 1) > width:
            raise ValueError(f"Not enough width for the given number of columns: {sum(self.gridW) + (self.cols - 1)} > {width}")
        self.gapH = (width - sum(self.gridW) - (self.cols - 1)) // (self.cols - 1) if self.cols > 1 else 0
        self.gapV = (height - sum(self.gridH) - (self.rows - 1)) // (self.rows - 1) if self.rows > 1 else 0

    def places(self, n: int) -> list[tuple[int, int]]:
        pos = []
        if n > self.rows * self.cols:
            raise ValueError(f"Number of elements exceeds grid capacity: {n} > {self.rows * self.cols}")
        y = 0
        for r in range(self.rows):
            x = 0
            for c in range(self.cols):
                pos.append((x, y))
                if len(pos) == n:
                    return pos
                x += self.gridW[c] + self.gapH
            y += self.gridH[r] + self.gapV
        return pos