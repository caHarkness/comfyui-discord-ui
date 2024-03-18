import re

def make_replacements(input_string, pat, replacement):
    if input_string is None:
        return input_string

    using = input_string
    match = re.search(pat, using)
    while match is not None:
        using = re.sub(pat, str(replacement), using)
        match = re.search(pat, using)
    return using

def parse_input(input_string, all_options={}):
    '''
    example:
    384p steps++ > ((photorealistic)) 1girl close portrait, white bob haircut, red eyes, blood dripping from face, bloody lips, black choker, f1.8 -((2d)), drawn, noise, grit, dull, washed out, low contrast, blurry, deep-fried, hazy, malformed, warped, deformed x8

    3 critical parts to this:
    
    1. 384p steps++ >
    2. ((photorealistic)) 1girl close portrait...
    3. -((2d)), drawn...
    4. x8

    In fig. 4, the trailing xN will always set the batch size to N
    In fig. 1, the options to control how the request is made are space delimited, everything before the first ">"
    In fig. 3. the negative prompt is everything after the **FIRST OCCURRENCE** of " -" (space and hypen)
    In fig. 2. the positive prompt is everything that's between the options
    '''

    output = all_options
    using = input_string

    # Get batch size from long string:
    batch_re = r" x([1-9][0-9]?)$"
    match = re.search(batch_re, using)
    if match is not None:
        output["batch_size"] = int(match.group(1))
        using = re.sub(batch_re, "", using)


    # Get options from long string:
    option_re = r"^((.+)>)"
    options = ""
    match = re.search(option_re, using)
    if match is not None:
        options = match.group(2)
        using = re.sub(option_re, "", using)

    # Get negative from long string:
    negative_re = r"( -(.+))$"
    match = re.search(negative_re, using)
    if match is not None:
        output["negative"] = match.group(2)
        using = re.sub(negative_re, "", using)

    # Get supporting from long string:
    supporting_re = r"( \:\:(.+))$"
    match = re.search(supporting_re, using)
    if match is not None:
        output["supporting"] = match.group(2)
        using = re.sub(supporting_re, "", using)

    using = using.strip()
    output["positive"] = using

    # Set minimum dimension:
    if output["width"] == output["height"]:
        match = re.search(r"([1-9][0-9]{2,3})p", options)
        if match is not None:
            s = int(match.group(1))
            output["width"] = s
            output["height"] = s

        # Limit the width and height to
        '''
        for k in ["width", "height"]:
            if f"max_{k}" in output:
                output[k] = output[f"max_{k}"] if output[k] > output[f"max_{k}"] else output[k]
        '''

    match = re.search(r"([0-9]{1,2})(x|\:)([0-9]{1,2})", options)
    if match is not None:
        # Use the smallest dimension for calculations:
        size = output["width"] if output["width"] <= output["height"] else output["height"]

        r_num = int(match.group(1))
        r_den = int(match.group(3))

        # Largest dimension not to exceed the size:
        if r_num > r_den:
            ratio = 1.0 * r_num / r_den
            output["width"] = size
            output["height"] = size * (1 / ratio)
        elif r_num < r_den:
            ratio = 1.0 * r_num / r_den
            output["width"] = size * ratio
            output["height"] = size

        '''
        if "max_width" in output or "max_height" in output:
            # Largest dimension not to exceed the size:
            if r_num > r_den:
                ratio = 1.0 * r_num / r_den
                output["width"] = size
                output["height"] = size * (1 / ratio)
            elif r_num < r_den:
                ratio = 1.0 * r_num / r_den
                output["width"] = size * ratio
                output["height"] = size
        else:
            # Size will be smallest dimension:
            if r_num > r_den:
                ratio = 1.0 * r_num / r_den
                output["width"] = size * ratio
                output["height"] = size
            elif r_num < r_den:
                ratio = 1.0 * r_num / r_den
                output["width"] = size
                output["height"] = size * (1.0 / ratio)
        '''

    # If the user specifies NNNxNNNp:
    match = re.search(r"([0-9]{1,})(x)([0-9]{1,})p", options)
    if match is not None:
        output["width"] = int(match.group(1))
        output["height"] = int(match.group(3))

        '''
        for k in ["width", "height"]:
            if f"max_{k}" in output:
                output[k] = output[f"max_{k}"] if output[k] > output[f"max_{k}"] else output[k]
        '''


    overwrite_re = r"([A-Za-z_]{1,})=?([0-9\.]{1,})"
    for (k, v) in re.findall(overwrite_re, options):
        output[k] = float(v)

    # Limit the rest of the options via their max:
    '''
    for k in ["steps", "cfg", "batch_size"]:
        if f"max_{k}" in output:
            output[k] = output[f"max_{k}"] if int(output[k]) > int(output[f"max_{k}"]) else output[k]
    '''

    # Only allow certain characters"
    for k in ["positive", "supporting", "negative"]:
        if k in output:
            output[k] = make_replacements(output[k], r"[^A-Za-z0-9 \-\.\(\),]", "")


    # Process keys like "max_somekey" to set maximum "somekey"
    starting_keys = []
    for key in output.keys():
        starting_keys.append(key)

    for key in starting_keys:
        if re.match(r"^max_", key):
            max_key = key
            target_key = key[4:]
            # print(target_key)

            if output[max_key] is not None:
                if float(output[target_key]) > float(output[max_key]):
                    output[target_key] = output[max_key]

    return output
