import yaml
import subprocess
import tempfile
import os
import shutil
from input_sources import get_input_command
from commands import (
    generate_incremental_text_cmd,
    generate_filter_cmd,
    generate_crop_command,
    generate_speed_command,
    generate_rotate_command,
    generate_scale_command,
    generate_setsar_command,
    overlay_video_cmd,
)


def parse_yaml(file_path):
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def tokenize_data(data, tokens):
    if "render" in data:
        tokens.append(("render", data["render"]))
    elif "overlay" in data:
        tokens.append(("start_overlay", data["overlay"]))
        for input_data in data["overlay"]:
            tokenize_data(input_data, tokens)
        tokens.append(("end_overlay", data["overlay"]))
    elif "combine" in data:
        combine_data = data["combine"]
        tokens.append(("start_combine", combine_data))
        for input_data in combine_data["inputs"]:
            tokenize_data(input_data, tokens)
        tokens.append(("end_combine", combine_data))


def tokenize_yaml(yaml_data):
    tokens = []
    tokenize_data({"combine": yaml_data["combine"]}, tokens)
    return tokens


def process_tokens(tokens, renderer, output):
    stack = []
    for token in tokens:
        token_type, token_data = token

        if token_type == "render":
            print("Rendering")
            src = token_data["src"]
            start_time = token_data.get("from",0)
            duration = token_data["duration"]
            text = token_data.get("text")

            speed = token_data.get("speed")
            crop = token_data.get("crop")
            rotate = token_data.get("rotate")
            scale = token_data.get("scale")
            aspect_ratio = token_data.get("aspect_ratio")

            temp_file = tempfile.mkstemp(suffix=".mp4")[1]
            renderer = token_data.get("renderer") or renderer
            input_command = get_input_command(src, start_time)

            filter_complex = ""
            if speed:
                filter_complex += generate_speed_command(speed)
            if rotate:
                filter_complex += "," + generate_rotate_command(rotate)
            if scale:
                filter_complex += "," + generate_scale_command(scale)
            if crop:
                filter_complex += "," + generate_crop_command(crop)
            if text:
                filter_complex += "," + generate_incremental_text_cmd(text)
            if aspect_ratio is not None:
                filter_complex += "," + generate_setsar_command(aspect_ratio)

            if filter_complex.startswith(","):
                filter_complex = filter_complex[1:]  # Remove leading comma

            filter_complex = f'-filter_complex \"{filter_complex}\"' if filter_complex else ""

            ffmpeg_cmd = f"ffmpeg -y {input_command} -t {duration} {filter_complex} -c:v {renderer} {temp_file}"
            print(f"Rendering: {ffmpeg_cmd}")
            subprocess.run(ffmpeg_cmd, shell=True, check=True)
            stack.append(temp_file)

        elif token_type == "start_overlay":
            print("start_overlay")
            stack.append(token_type)

        elif token_type == "end_overlay":
            print("end overtlay")
            # Create video streams from token_data and combine them using the overlay filter.
            overlay_files = []
            while stack and stack[-1] != "start_overlay":
                overlay_files.append(stack.pop())
            if stack:
                stack.pop()  # Remove 'start_overlay' from the stack

            background_file = overlay_files[0]
            overlay_file = overlay_files[-1]

            # Ensure the temp_file for the overlay is different from the input files
            temp_file = tempfile.mkstemp(suffix=".mp4")[1]
            while temp_file in overlay_files:
                temp_file = tempfile.mkstemp(suffix=".mp4")[1]

            overlay_cmd = overlay_video_cmd(background_file, overlay_file, temp_file, renderer)
            subprocess.run(overlay_cmd, shell=True, check=True)

            for overlay_file in overlay_files:
                os.remove(overlay_file)

            stack.append(temp_file)


        elif token_type == "start_combine":
            print("starting combining")
            stack.append(token_type)

        elif token_type == "end_combine":
            print("end combining")
            temp_files = []
            while stack and stack[-1] != "start_combine":
                temp_files.append(stack.pop())
            temp_files.reverse()

            if stack:
                stack.pop()  # Remove 'start_combine' from the stack

            count = 0
            if len(temp_files) > 1:
                transition = token_data["transition"]
                renderer = token_data.get("renderer") or renderer
                #
                temp_file = tempfile.mkstemp(suffix=".mp4")[1]
                input_files = " ".join(
                    [f"-i {input_file}" for input_file in temp_files]
                )
                print(len(input_files))
                # filter_complex = ";".join([f"[{i}:v]setpts=PTS-STARTPTS[v{i}]" for i in range(len(temp_files))])
                filter_complex = generate_filter_cmd(
                    transition,
                    temp_files,
                )

                concat_filter = "".join([f"[v{i}]" for i in range(len(temp_files))])
                filter_complex += (
                    f";{concat_filter}concat=n={len(temp_files)}:v=1:a=0[vout]"
                )
                ffmpeg_cmd = f'ffmpeg -y {input_files} -filter_complex "{filter_complex}" -map "[vout]" -c:v {renderer} {temp_file}'
                print(ffmpeg_cmd)
                subprocess.run(ffmpeg_cmd, shell=True, check=True)
                count += 1
                print(count)

                for input_file in temp_files:
                    os.remove(input_file)

                stack.append(temp_file)
            else:
                stack.append(temp_files[0])

    if len(stack) == 1:
        print("Moving file to output")
        shutil.move(stack[0], output)
    else:
        print(stack)
        print("Error: Stack is not empty!")


