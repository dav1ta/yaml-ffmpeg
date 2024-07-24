from math import pi as PI


def generate_filter_cmd(
    filter_name, input_files_list, transition_duration=2.0, overlay=False
):
    if overlay:
        x, y = map(int, overlay.split(":"))
        filter_complex = ";".join(
            [f"[{i}:v]overlay={x}:{y}[v{i}]" for i in range(len(input_files_list))]
        )

    elif filter_name == "fade_in":
        filter_complex = ";".join(
            [
                f"[{i}:v]fade=t=in:st=0:d={transition_duration}[v{i}]"
                for i in range(len(input_files_list))
            ]
        )
        print(filter_complex)
    elif filter_name == "fade_out":
        filter_complex = ";".join(
            [
                f"[{i}:v]fade=t=out:st=0:d={transition_duration}[v{i}]"
                for i in range(len(input_files_list))
            ]
        )
    elif filter_name == "zoom":
        filter_complex = ";".join(
            [
                f"[{i}:v]zoompan=z='zoom+0.001':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={transition_duration}[v{i}]"
                for i in range(len(input_files_list))
            ]
        )
    elif filter_name == "crossfade":
        filter_complex = ";".join(
            [
                f"[{i}:v][{i + 1}:v]overlay=x=0:y=0:enable='between(t,{i * transition_duration},{i * transition_duration + transition_duration})'[v{i}]"
                for i in range(len(input_files_list) - 1)
            ]
        )
    else:
        filter_complex = ";".join(
            [f"[{i}:v]setpts=PTS-STARTPTS[v{i}]" for i in range(len(input_files_list))]
        )


    return filter_complex


def generate_text_overlay_cmd(
    input_files_list,
    text=None,
    font_size=24,
    font_color="white",
    duration=None,
    x=10,
    y=10,
):
    if text is None:
        text = "Sample Text"

    if duration is None:
        duration_expr = ""
    else:
        duration_expr = f":enable='between(t,0,{duration}')"
    filter_complex = ";".join(
        [
            f"[{i}:v]drawtext=text='{text}':x={x}:y={y}:fontsize={font_size}:fontcolor={font_color}{duration_expr}[v{i}]"
            for i in range(len(input_files_list))
        ]
    )

    return filter_complex


def generate_incremental_text_cmd(txt):
    text = txt.get("value", "Sample Text")
    font_size = txt.get("font_size", 30)
    font_color = txt.get("font_color", "white")
    duration = txt.get("duration")
    x = txt.get("x", 10)
    y = txt.get("y", 10)
    position = txt.get("position")
    box = 1 if txt.get("background") else 0
    border_color = txt.get("border_color", "black")
    border_width = txt.get("border_width", 4)

    position_map = {
        "center": f"(w-text_w)/2:(h-text_h)/2",
        "top_left": "10:10",
        "top_right": "(main_w-text_w-10):10",
        "bottom_left": "10:(main_h-text_h-10)",
        "bottom_right": "(main_w-text_w-10):(main_h-text_h-10)",
    }

    xy_values = position_map.get(position, f"{x}:{y}")
    x, y = xy_values.split(":")

    duration_expr = f":enable='between(t,0,{duration})'" if duration else ""

    drawtext_filter = f"drawtext=text='{text}':x={x}:y={y}:fontsize={font_size}:fontcolor={font_color}{duration_expr}:box={box}:borderw={border_width}:bordercolor={border_color}"

    return drawtext_filter


def generate_speed_command(speed):
    return f"[0:v]setpts={1/speed}*PTS[v];[0:a]atempo={speed}[a]"


def generate_rotate_command(rotate):
    return f"[v]rotate={rotate*PI/180}[v]"


def generate_scale_command(scale):
    return f'scale={scale["w"]}:{scale["h"]}'


def generate_crop_command(crop):
    w = crop.get("w")
    h = crop.get("h")
    x = crop.get("x", "(iw-ow)/2")  # center if not specified
    y = crop.get("y", "(ih-oh)/2")  # center if not specified
    return f"crop={w}:{h}:{x}:{y}"


def generate_setsar_command(aspect_ratio):
    return f"setsar={aspect_ratio}"



def overlay_video_cmd(main_video, overlay_video, output_file, renderer):
    ffmpeg_cmd = f"""ffmpeg -i {main_video} -i {overlay_video} -filter_complex "[1:v]colorkey=0x00ff00:0.3:0.1[ckout];[0:v][ckout] overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2" -c:v {renderer} {output_file}"""
    return ffmpeg_cmd



