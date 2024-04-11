#THIS VSCODE SCRIPT MUST BE RUN WITH THE BLENDER EXTENSION ADD ON, FAKE BLENDER MODULE IS ALSO REQUIRED
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
outputd1 = r"C:\Users\Kevin Kyle\Desktop\It's NeRF or Nothin'!\results\images"
outputd2 = r"C:\Users\Kevin Kyle\Desktop\It's NeRF or Nothin'!\results\images_2"
outputd4 = r"C:\Users\Kevin Kyle\Desktop\It's NeRF or Nothin'!\results\images_4"
outputd8 = r"C:\Users\Kevin Kyle\Desktop\It's NeRF or Nothin'!\results\images_8"
fp = r"C:\Users\Kevin Kyle\Desktop\It's NeRF or Nothin'!\results"

#Defining variables from blender workspace
scene = bpy.context.scene
camera = bpy.context.scene.camera
fileformat = "PNG" #JPEG or PNG

#Script parameters
numpics = 10
camera_radius = 20#Distance from the central object
res_x = 1920
res_y = 1120

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


#Conversion between camera view and world view
def listify_matrix(matrix):
    matrix_list = []
    for row in matrix:
      matrix_list.append(list(row))
    return matrix_list
#Obtain init camera properties
def get_camera_intrinsics(scene, camera):
    
        camera_angle_x = camera.data.angle_x
        camera_angle_y = camera.data.angle_y

        # camera properties
        f_in_mm = camera.data.lens # focal length in mm
        scale = scene.render.resolution_percentage / 100
        width_res_in_px = scene.render.resolution_x * scale # width
        height_res_in_px = scene.render.resolution_y * scale # height
        optical_center_x = width_res_in_px / 2
        optical_center_y = height_res_in_px / 2

        # pixel aspect ratios
        size_x = scene.render.pixel_aspect_x * width_res_in_px
        size_y = scene.render.pixel_aspect_y * height_res_in_px
        pixel_aspect_ratio = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y

        # sensor fit and sensor size (and camera angle swap in specific cases)
        if camera.data.sensor_fit == 'AUTO':
            sensor_size_in_mm = camera.data.sensor_height if width_res_in_px < height_res_in_px else camera.data.sensor_width
            if width_res_in_px < height_res_in_px:
                sensor_fit = 'VERTICAL'
                camera_angle_x, camera_angle_y = camera_angle_y, camera_angle_x
            elif width_res_in_px > height_res_in_px:
                sensor_fit = 'HORIZONTAL'
            else:
                sensor_fit = 'VERTICAL' if size_x <= size_y else 'HORIZONTAL'

        else:
            sensor_fit = camera.data.sensor_fit
            if sensor_fit == 'VERTICAL':
                sensor_size_in_mm = camera.data.sensor_height if width_res_in_px <= height_res_in_px else camera.data.sensor_width
                if width_res_in_px <= height_res_in_px:
                    camera_angle_x, camera_angle_y = camera_angle_y, camera_angle_x

        # focal length for horizontal sensor fit
        if sensor_fit == 'HORIZONTAL':
            sensor_size_in_mm = camera.data.sensor_width
            s_u = f_in_mm / sensor_size_in_mm * width_res_in_px
            s_v = f_in_mm / sensor_size_in_mm * width_res_in_px * pixel_aspect_ratio

        # focal length for vertical sensor fit
        if sensor_fit == 'VERTICAL':
            s_u = f_in_mm / sensor_size_in_mm * width_res_in_px / pixel_aspect_ratio
            s_v = f_in_mm / sensor_size_in_mm * width_res_in_px

        camera_intr_dict = {
            'camera_angle_x': camera_angle_x,
            'camera_angle_y': camera_angle_y,
            'fl_x': s_u,
            'fl_y': s_v,
            'k1': 0.0,
            'k2': 0.0,
            'p1': 0.0,
            'p2': 0.0,
            'cx': optical_center_x,
            'cy': optical_center_y,
            'w': width_res_in_px,
            'h': height_res_in_px,
            #'aabb_scale': scene.aabb
        }

        return {'camera_angle_x': camera_angle_x} if scene.nerf else camera_intr_dict


   
    # camera extrinsics (transform matrices)
def get_camera_extrinsics(camera, filepath):

        frame_data = {
                'file_path': filepath,
                'transform_matrix': listify_matrix( camera.matrix_world )
        }
        return frame_data
        
## FOR SCALING/RENDERING IMAGES
def renderImage(downScale: int, location, index:int):
    scene.render.resolution_x = res_x//downScale
    scene.render.resolution_y = res_y//downScale
    if(fileformat == "PNG"):
        bpy.context.scene.render.image_settings.color_mode = 'RGBA'  # Make sure to use RGBA for transparency
        bpy.context.scene.render.film_transparent = True
        bpy.context.scene.render.filepath = join(location, "render_{}.png".format(index + 1))
    else:
        bpy.context.scene.render.filepath = join(location, "render_{}.jpeg".format(index + 1))
    # Render the image
    bpy.ops.render.render(write_still=True)

out_data = get_camera_intrinsics(scene, camera)
out_data['frames'] = []
obj = bpy.data.objects.get('model')

# Set rendering settings
bpy.context.scene.render.image_settings.file_format = fileformat
#bpy.context.scene.render.image_settings.color_mode = 'RGBA'  # Make sure to use RGBA for transparency
bpy.context.scene.render.film_transparent = True
#bpy.context.scene.render.filepath = os.path.join(fp, "render_")

for i in range(0, numpics):
    # Generate random angles for camera rotation
    theta = radians(uniform(0, 360))
    phi = radians(uniform(0, 180))
    psi = radians(uniform(0, 360))

    # Calculate camera position
    camera_x = camera_radius * sin(phi) * cos(theta)
    camera_y = camera_radius * sin(phi) * sin(theta)
    camera_z = camera_radius * cos(phi)

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

    if(fileformat == "JPEG"):
            out_data['frames'].append(get_camera_extrinsics(camera, "images/render_{}.jpeg".format(i + 1)))
    else:
         out_data['frames'].append(get_camera_extrinsics(camera, "images/render_{}.png".format(i + 1)))


with open(fp + '/' + 'transforms.json', 'w') as out_file:
    json.dump(out_data, out_file, indent=4)

# Reset the file path to avoid issues in future renders
bpy.context.scene.render.filepath = ""
print("Mission complete")


