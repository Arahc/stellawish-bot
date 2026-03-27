from abc import ABC, abstractmethod

class RatingCalcer(ABC):
    @abstractmethod
    def __call__(self, score) -> int | float:
        pass

class defaultRaCalcer(RatingCalcer):
    def __call__(self, score) -> int:
        return score.chart.getRating(score.acc)

class YangRaCalcer(RatingCalcer):
    def __call__(self, score) -> float:
        return round(max(0, score.chart.diff * min(score.acc - 100, score.dxScore / score.chart.getMaxDXscore())), 2)

class EightScoreRaCalcer(RatingCalcer):
    def __call__(self, score) -> int:
        res = 0
        if score.acc >= 100.98:
            res += 3
        elif score.acc >= 100.95:
            res += 2
        elif score.acc >= 100.9:
            res += 1
        if score.fc == "fcp":
            res += 1
        elif score.fc == "ap" or score.fc == "app":
            res += 2
        star = score.getStar()
        if star >= 5:
            res += 3
        elif star >= 4:
            res += 2
        elif star >= 3:
            res += 1
        return res