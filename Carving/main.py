import sys
from carpe_carving import Carving

def main(image):
    object = Carving(image)
    object.carve_eml(0, 1000000000)         # current_offset, next_offset
    # 생각해야 할 것은 이미지 하나에서 매칭되는 만큼 계속 추출을 할텐데 그건 어떻게?

if __name__ == "__main__":
    main(sys.argv[1])

