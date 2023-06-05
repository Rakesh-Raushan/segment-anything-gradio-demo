# Segment anything demo with Gradio

import sys, os
import gradio as gr
import numpy as np
import torch
import matplotlib.pyplot as plt
import cv2
import requests
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator, SamPredictor
sys.path.append("..")

def show_anns(anns):
    if len(anns) == 0:
        return
    sorted_anns = sorted(anns, key=(lambda x: x['area']), reverse=True)
    #ax = plt.gca()
    #ax.set_autoscale_on(False)

    img = np.ones((sorted_anns[0]['segmentation'].shape[0], sorted_anns[0]['segmentation'].shape[1], 4))
    img[:,:,3] = 0
    for ann in sorted_anns:
        m = ann['segmentation']
        color_mask = np.concatenate([np.random.random(3), [0.35]])
        img[m] = color_mask
    #ax.imshow(img)
    return img

def read_img(image):
    image = cv2.imread('images/dog.jpg')
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return image

def download_model(url, save_path):
    response = requests.get(url)
    with open(save_path, "wb") as file:
        file.write(response.content)

# Define the URL of the model file on GitHub
github_url = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth"

# Specify the local path where you want to save the downloaded model file
local_path = "sam_vit_h_4b8939.pth"

# Download the model file from the GitHub URL if it does not exist
if not os.path.exists(local_path):
    download_model(github_url, local_path)

def get_masks(image):
    sam_checkpoint = local_path
    model_type = "vit_h"
    device = "cpu"
    sam = sam_model_registry[model_type](checkpoint=sam_checkpoint)
    sam.to(device=device)
    mask_generator = SamAutomaticMaskGenerator(sam)
    masks = mask_generator.generate(image)
    return masks




def segment_all(image):
    # inp_img = read_img(image)
    masks = get_masks(image)
    list_of_iou = [mask['predicted_iou'] for mask in masks]
    stability_scores = [mask['stability_score'] for mask in masks]
    mean_iou = round(sum(list_of_iou)/len(list_of_iou),3)
    mean_stability_score = round(sum(stability_scores)/len(stability_scores),3)

    #resized_masks = cv2.resize(masks, (image.shape[1], image.shape[0]))
    return [show_anns(masks), str(f"Mean IoU: {mean_iou} \n Mean stability score: {mean_stability_score}")]#str(mean_iou), str(mean_stability_score)]


output_image = gr.Image(label="Segmented Image")
# mean_iou_text = gr.Textbox(label="Mean IoU")
# mean_ss_text = gr.Textbox(label="Mean Stability Scores")
model_metrics_text = gr.Textbox(label="Segmentation Metrics")

interface = gr.Interface(fn=segment_all, 
             inputs="image", 
             outputs=[output_image, model_metrics_text],#mean_iou_text, mean_ss_text],
             title="Image Segmentation demo using segment_anything",
             description="Upload an image to segment.",
             allow_flagging='manual',
            theme="huggingface",
            layout="vertical")
interface.launch()
interface.logo("path_to_logo.png")  # Replace "path_to_logo.png" with the actual path to your logo image
interface.input_description("input_image", "Upload image here")
interface.output_description("output_image", "Segmented image")
