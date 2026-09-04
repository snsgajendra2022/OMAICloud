from om_ai.perception.vision.manager import VisionManager


vision = VisionManager()


result = vision.process_image(
    "test-image.png"
)


print(result)