import os
import json


def any_to_num(input_str, fallback_num_s):
    num_s = ""
    num_n = 0

    for c in str(input_str):
        if c.isdigit():
            num_s += c
            num_n += int(c)
        else:
            num_n += (ord(c) / len(str(ord(str(c)))))

    if num_s == "":
        num_s = fallback_num_s

    return num_n, int(num_s)


def store_json(output_path, new_data, clear=False, data_limit=20, merge_key="misc"):
    if not os.path.exists(output_path):
        with open(output_path, "w") as id:
            json.dump(new_data, id, sort_keys=True, indent=4)

    if clear:
        with open(output_path, "w") as d:
            json.dump(new_data, d, sort_keys=True, indent=4)

        return new_data

    with open(output_path) as cd:
        curr_content = json.load(cd)

    temp_data = curr_content
    if merge_key not in temp_data.keys():
        temp_data[merge_key] = []

    for k in new_data.keys():
        if new_data[k] not in temp_data[merge_key]:

            temp_data[merge_key].append(new_data[k])

    temp_data[merge_key] = temp_data[merge_key][-data_limit:]

    with open(output_path, "w") as d:
        json.dump(temp_data, d, sort_keys=True, indent=4)

    return temp_data


def get_abs_paths(root_path, f_format=".wav"):
    file_paths = []

    for root, dirs, files in os.walk(root_path):
        for f in files:
            if f.endswith(f_format):
                pth = os.path.abspath(root) +"/"+ f
                file_paths.append(pth)

    return file_paths


def update_conf(conf_file_path, data_path, parameter, p_value):
    print("Updating: " + str(conf_file_path))

    with open(conf_file_path) as d:
        conf_data = json.load(d)

    tmp_data = conf_data
    d.close()

    tmp_data[parameter] = p_value

    with open(data_path, "w") as d:
        json.dump(tmp_data, d)

    d.close()