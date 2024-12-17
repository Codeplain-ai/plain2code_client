DEFINITIONS = 'Definitions:'
NON_FUNCTIONAL_REQUIREMENTS = 'Non-Functional Requirements:'
TEST_REQUIREMENTS = 'Test Requirements:'
FUNCTIONAL_REQUIREMENTS = 'Functional Requirements:'


def collect_linked_resources(plain_section):
    linked_resources = []

    if isinstance(plain_section, dict):
        for key, value in plain_section.items():
            if key == 'linked_resources':
                linked_resources.extend(value)
            else:
                linked_resources.extend(collect_linked_resources(value))
    elif isinstance(plain_section, list):
        for item in plain_section:
            linked_resources.extend(collect_linked_resources(item))

    return linked_resources


def get_linked_resources(plain_sections):
    if not isinstance(plain_sections, dict):
        raise ValueError("plain_sections must be a dictionary.")
    
    linked_resources_list = []
    for key, value in plain_sections.items():
        linked_resources = collect_linked_resources(value)
        for resource in linked_resources:
            resource_found = False
            for resource_map in linked_resources_list:
                if resource['text'] == resource_map['text']:
                    if resource['target'] != resource_map['target']:
                        raise Exception(f"The file {resource['target']} is linked to multiple linked resources with the same text: {resource['text']}")
                elif resource['target'] == resource_map['target']:
                    if resource['text'] != resource_map['text']:
                        raise Exception(f"The linked resource {resource['text']} is linked to multiple files: {resource_map['target']}")
                else:
                    continue

                if resource_found:
                    raise Exception("Duplicate linked resource found: " + resource['text'] + " (" + resource['target'] + ")")

                resource_found = True
                resource_map['sections'].append(key)

            if not resource_found:
                linked_resources_list.append({
                    'text': resource['text'],
                    'target': resource['target'],
                    'sections': [key]
                })

    return linked_resources_list