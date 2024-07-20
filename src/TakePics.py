#THIS VSCODE SCRIPT MUST BE RUN WITH THE BLENDER EXTENSION, FAKE BLENDER MODULE IS ALSO REQUIRED
#Setup tutorial: https://www.youtube.com/watch?v=YUytEtaVrrc 
#Install "Blender Development" VScode extension by Jacques Lucke
#pip install fake-bpy-module-latest
#Connect vscode to blender as seen in video -> follow video if run into issues
import bpy
import os
import math
import json
import datetime
from os.path import join, exists
from math import radians, sin, cos
from mathutils import Vector
from random import uniform

# Specify the output directory for rendered images
outputd1 = r"C:\Users\kev\Desktop\NeRF_NVIDIA\results\images"
outputd2 = r"C:\Users\kev\Desktop\NeRF_NVIDIA\results\images_2"
outputd4 = r"C:\Users\kev\Desktop\NeRF_NVIDIA\results\images_4"
outputd8 = r"C:\Users\kev\Desktop\NeRF_NVIDIA\results\images_8"
fp = r"C:\Users\kev\Desktop\NeRF_NVIDIA\results"

# Defining variables from the Blender workspace
scene = bpy.context.scene
camera = bpy.context.scene.camera
fileformat = "PNG"  # JPEG or PNG

# Script parameters
numpics = 400
camera_radius = 30  # Distance from the central object'
min_dist = 30
max_dist = 500
res_x = 1920
res_y = 1120
variable_distance = True  # Set this to True for variable distances

# Check if light with the given name exists
light_name = "MyLightObject"
light_object = bpy.data.objects.get(light_name)

if light_object is None:
    # If light doesn't exist, create a new one
    # Create a new light datablock
    light_data = bpy.data.lights.new(name=light_name, type='POINT')
    # Create a new object with the light datablock
    light_object = bpy.data.objects.new(name="MyLightObject", object_data=light_data)
    bpy.context.scene.collection.objects.link(light_object)
    # Set light properties (optional)
    light_object.location = (0, 0, 5)  # Example location
    light_data.energy = 500  # Example light intensity
    print("Light configured")
else:
    print("Light already exists in the scene:", light_name)

# Function to render an image
def renderImage(downScale: int, location, index: int):
    scene.render.resolution_x = res_x // downScale
    scene.render.resolution_y = res_y // downScale
    if fileformat == "PNG":
        bpy.context.scene.render.image_settings.color_mode = 'RGBA'  # Make sure to use RGBA for transparency
        bpy.context.scene.render.film_transparent = True
        bpy.context.scene.render.filepath = join(location, "render_{}.png".format(index + 1))
    else:
        bpy.context.scene.render.filepath = join(location, "render_{}.jpeg".format(index + 1))
    # Render the image
    bpy.ops.render.render(write_still=True)

obj = bpy.data.objects.get('model')

# Set rendering settings
bpy.context.scene.render.image_settings.file_format = fileformat
bpy.context.scene.render.film_transparent = True

for i in range(0, numpics):
    # Generate random angles for camera rotation
    theta = radians(uniform(0, 360))
    phi = radians(uniform(0, 180))
    psi = radians(uniform(0, 360))

    # Calculate camera distance
    distance = camera_radius
    if variable_distance:
        distance = uniform(min_dist, max_dist)  # Random distance between 10 and 30 units

    # Calculate camera position
    camera_x = distance * sin(phi) * cos(theta)
    camera_y = distance * sin(phi) * sin(theta)
    camera_z = distance * cos(phi)

    # Set camera location
    bpy.context.scene.camera.location = (camera_x, camera_y, camera_z)

    # Point the camera towards the central object (origin)
    direction = Vector((0, 0, 0)) + bpy.context.scene.camera.location
    rot_quat = direction.to_track_quat('Z', 'Y')

    # Set the camera rotation using the quaternion
    bpy.context.scene.camera.rotation_euler = rot_quat.to_euler()

    # Save/scale images and their orientation
    renderImage(1, outputd1, i)
    renderImage(2, outputd2, i)
    renderImage(4, outputd4, i)
    renderImage(8, outputd8, i)

# Reset the file path to avoid issues in future renders
bpy.context.scene.render.filepath = ""
print("Mission complete")
