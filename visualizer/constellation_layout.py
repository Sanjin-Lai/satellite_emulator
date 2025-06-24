class ConstellationLayout:
    @classmethod
    def generate(cls, orbit_number: int, sat_per_orbit: int):
        """
        进行星座拓扑的构建
        :param orbit_number: 轨道的数量
        :param sat_per_orbit: 每轨道的卫星的数量
        """
        start_x = -1
        start_y = 1
        x_increase = 1 / sat_per_orbit
        y_decrease = -1 / orbit_number
        positions = []
        for i in range(orbit_number):
            for j in range(sat_per_orbit):
                point_x = start_x + x_increase * i
                point_y = start_y + y_decrease * j
                if j == sat_per_orbit - 1:
                    point_x += 0.01
                positions.append((point_x, point_y))
        return positions


if __name__ == "__main__":
    result = ConstellationLayout.generate(orbit_number=3, sat_per_orbit=3)
    print(result)

