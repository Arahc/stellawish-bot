class GridManager:
    def __init__(self, width: int, height: int, element_w: int, element_h: int, rows: int, cols: int):
        self.W = width
        self.H = height
        self.gridW = element_w
        self.gridH = element_h
        self.rows = rows
        self.cols = cols
        if rows * (self.gridH + 1) > height:
            raise ValueError("Not enough height for the given number of rows")
        if cols * (self.gridW + 1) > width:
            raise ValueError("Not enough width for the given number of columns")
        self.gapH = (width - cols * self.gridW) // (cols - 1) if cols > 1 else 0
        self.gapV = (height - rows * self.gridH) // (rows - 1) if rows > 1 else 0
    
    def places(self, n: int) -> list[tuple[int, int]]:
        pos = []
        if n > self.rows * self.cols:
            raise ValueError("Number of elements exceeds grid capacity")
        for r in range(self.rows):
            for c in range(self.cols):
                x = c * (self.gridW + self.gapH)
                y = r * (self.gridH + self.gapV)
                pos.append((x, y))
                if len(pos) == n:
                    return pos
        return pos